from __future__ import annotations

import base64
import hashlib
import inspect
import os
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import List, Optional

os.environ.setdefault("TORCH_DISABLE_WEIGHTS_ONLY_LOAD", "1")

try:  # ensure torch.load defaults remain backward compatible
    import torch
except Exception:  # pragma: no cover - torch optional in mock mode
    torch = None  # type: ignore[assignment]
else:
    _orig_torch_load = torch.load

    if "weights_only" in inspect.signature(_orig_torch_load).parameters:
        def _patched_torch_load(*args, **kwargs):
            kwargs.setdefault("weights_only", False)
            return _orig_torch_load(*args, **kwargs)

        torch.load = _patched_torch_load  # type: ignore[assignment]

import cv2
import numpy as np
from easyocr import Reader
from loguru import logger
from ultralytics import YOLO

from app.core.config import settings

try:  # PyTorch 2.6 defaults to weights_only=True which breaks Ultralytics checkpoints
    from torch.serialization import add_safe_globals
except Exception:  # pragma: no cover - torch missing or old version
    add_safe_globals = None  # type: ignore[assignment]

try:
    from ultralytics.nn.tasks import DetectionModel
except Exception:  # pragma: no cover - legacy Ultralytics structure
    DetectionModel = None  # type: ignore[assignment]

try:
    from torch.nn.modules.container import Sequential
except Exception:  # pragma: no cover - depends on torch version
    Sequential = None  # type: ignore[assignment]

if add_safe_globals and torch:
    allowlist = [cls for cls in (DetectionModel, Sequential) if cls]
    if allowlist:
        try:
            add_safe_globals(allowlist)
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.debug("torch.add_safe_globals failed: {}", exc)


@dataclass
class VisionDetection:
    plate_text: str
    confidence: float


class VisionPipeline:
    """Lazy-loaded YOLOv8 + EasyOCR inference pipeline."""

    def __init__(self) -> None:
        self._model: Optional[YOLO] = None
        self._reader: Optional[Reader] = None
        self._lock = Lock()
        self._cache_lock = Lock()
        self._device = settings.yolo_device
        self._plate_classes: List[int] = settings.yolo_plate_classes
        self._conf = settings.yolo_conf_threshold
        self._max_side = settings.yolo_max_side
        self._crop_margin = max(0.0, settings.ocr_crop_margin)
        self._cache_ttl = max(0.0, settings.lpr_frame_cache_ms / 1000.0)
        self._last_fingerprint: Optional[str] = None
        self._last_detection: Optional[VisionDetection] = None
        self._last_detection_ts: float = 0.0

    def _ensure_loaded(self) -> None:
        if self._model and self._reader:
            return
        with self._lock:
            if self._model is None:
                weights = settings.yolo_weights_path
                try:
                    self._model = YOLO(weights)
                    try:
                        self._model.fuse()
                    except Exception:  # pragma: no cover - fuse unsupported
                        pass
                except Exception as exc:  # pragma: no cover
                    logger.warning("Failed to load YOLO weights {}: {}", weights, exc)
                    self._model = None
            if self._reader is None:
                try:
                    gpu = self._device.startswith("cuda") if isinstance(self._device, str) else False
                    self._reader = Reader(settings.ocr_languages, gpu=gpu)
                except Exception as exc:  # pragma: no cover
                    logger.warning("Failed to load EasyOCR reader: {}", exc)
                    self._reader = None

    def available(self) -> bool:
        self._ensure_loaded()
        return self._model is not None and self._reader is not None

    def detect_from_base64(self, image_base64: str) -> Optional[VisionDetection]:
        fingerprint = self._fingerprint(image_base64)
        cached = self._get_cached_detection(fingerprint)
        if cached:
            return cached
        frame = self._decode_frame(image_base64)
        if frame is None:
            return None
        detection = self.detect_from_frame(frame)
        if detection and fingerprint:
            self._store_cache(fingerprint, detection)
        return detection

    def detect_from_frame(self, frame: np.ndarray) -> Optional[VisionDetection]:
        self._ensure_loaded()
        if not self._model or not self._reader:
            return None
        frame = self._prepare_frame(frame)
        try:
            results = self._model.predict(
                frame,
                conf=self._conf,
                max_det=5,
                device=None if self._device == "auto" else self._device,
                verbose=False,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("YOLO inference failed: {}", exc)
            return None
        if not results:
            return None
        boxes = results[0].boxes
        if boxes is None or boxes.shape[0] == 0:
            return None
        best_idx = self._select_plate_index(boxes.cls.tolist(), boxes.conf.tolist())
        if best_idx is None:
            return None
        xyxy = boxes.xyxy[best_idx].cpu().numpy().astype(int)
        x1, y1, x2, y2 = xyxy
        h, w = frame.shape[:2]
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)
        if x2 <= x1 or y2 <= y1:
            return None
        crop = self._prepare_crop_for_ocr(frame, (x1, y1, x2, y2))
        if crop is None:
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                return None
        try:
            ocr_results = self._reader.readtext(crop, detail=1)
        except Exception as exc:  # pragma: no cover
            logger.warning("EasyOCR failed: {}", exc)
            return None
        if not ocr_results:
            return None
        # take best result
        best_text, best_prob = "", 0.0
        for (*_, text, prob) in ocr_results:
            normalized = self._normalize_plate(text)
            if not normalized:
                continue
            if prob > best_prob:
                best_text = normalized
                best_prob = prob
        if not best_text:
            return None
        det_conf = float(boxes.conf[best_idx].item())
        return VisionDetection(plate_text=best_text, confidence=round(min(1.0, det_conf * best_prob), 2))

    def _prepare_frame(self, frame: np.ndarray) -> np.ndarray:
        if self._max_side and frame.size:
            max_dim = max(frame.shape[:2])
            if max_dim > self._max_side and max_dim > 0:
                scale = self._max_side / float(max_dim)
                new_w = max(1, int(frame.shape[1] * scale))
                new_h = max(1, int(frame.shape[0] * scale))
                frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return frame

    def _prepare_crop_for_ocr(self, frame: np.ndarray, coords: tuple[int, int, int, int]) -> Optional[np.ndarray]:
        x1, y1, x2, y2 = coords
        h, w = frame.shape[:2]
        margin_x = int((x2 - x1) * self._crop_margin)
        margin_y = int((y2 - y1) * self._crop_margin)
        x1 = max(0, x1 - margin_x)
        y1 = max(0, y1 - margin_y)
        x2 = min(w, x2 + margin_x)
        y2 = min(h, y2 + margin_y)
        if x2 <= x1 or y2 <= y1:
            return None
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None
        try:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
            blurred = cv2.bilateralFilter(gray, d=5, sigmaColor=40, sigmaSpace=40)
            _, binary = cv2.threshold(
                blurred,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU,
            )
            return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        except Exception:  # pragma: no cover - OpenCV failures are rare
            return crop

    def _select_plate_index(self, class_ids: List[float], confidences: List[float]) -> Optional[int]:
        if not confidences:
            return None
        allowed = set(self._plate_classes) if self._plate_classes else None
        best_idx = None
        best_conf = -1.0
        for idx, conf in enumerate(confidences):
            cls_id = int(class_ids[idx]) if idx < len(class_ids) else -1
            if allowed is not None and cls_id not in allowed:
                continue
            if conf > best_conf:
                best_conf = conf
                best_idx = idx
        if best_idx is None and allowed is not None:
            return None
        return best_idx if best_idx is not None else int(np.argmax(confidences))

    @staticmethod
    def _normalize_plate(text: str) -> str:
        if not text:
            return ""
        cleaned = "".join(ch for ch in text.upper() if ch.isalnum() or ch.isspace())
        cleaned = " ".join(cleaned.split())
        if not cleaned:
            return ""
        alnum = cleaned.replace(" ", "")
        if len(alnum) < 4:
            return ""
        if not any(ch.isalpha() for ch in alnum) or not any(ch.isdigit() for ch in alnum):
            return ""
        if " " not in cleaned:
            boundary = VisionPipeline._letter_digit_boundary(cleaned)
            if boundary:
                cleaned = f"{cleaned[:boundary]} {cleaned[boundary:]}"
        return cleaned

    @staticmethod
    def _letter_digit_boundary(plate: str) -> int | None:
        for idx in range(1, len(plate)):
            if plate[idx - 1].isalpha() and plate[idx].isdigit():
                return idx
        return None

    @staticmethod
    def _decode_frame(image_base64: str) -> Optional[np.ndarray]:
        try:
            frame_bytes = base64.b64decode(image_base64)
            np_arr = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            return frame
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to decode base64 frame: {}", exc)
            return None

    def _fingerprint(self, payload: str) -> Optional[str]:
        if not payload or not self._cache_ttl:
            return None
        try:
            return hashlib.blake2b(payload.encode("utf-8"), digest_size=10).hexdigest()
        except Exception:
            return None

    def _get_cached_detection(self, fingerprint: Optional[str]) -> Optional[VisionDetection]:
        if not fingerprint or not self._cache_ttl:
            return None
        with self._cache_lock:
            if not self._last_fingerprint or not self._last_detection:
                return None
            if fingerprint != self._last_fingerprint:
                return None
            if monotonic() - self._last_detection_ts > self._cache_ttl:
                return None
            return self._last_detection

    def _store_cache(self, fingerprint: Optional[str], detection: VisionDetection) -> None:
        if not fingerprint or not self._cache_ttl:
            return
        with self._cache_lock:
            self._last_fingerprint = fingerprint
            self._last_detection = detection
            self._last_detection_ts = monotonic()


vision_pipeline = VisionPipeline()

__all__ = ["vision_pipeline", "VisionDetection"]
