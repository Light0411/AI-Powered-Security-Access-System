from __future__ import annotations

import base64
from typing import List

import cv2
import numpy as np
from insightface.app import FaceAnalysis
from loguru import logger
from onnxruntime import get_available_providers

from app.core.config import settings
from app.schemas import FaceEnrollRequest, FaceEnrollResponse, FaceMatch, FaceVerifyRequest, FaceVerifyResponse, UserFace

from .face_store import FaceEmbeddingStore
from .datastore import db


class FaceRecognitionService:
    def __init__(self) -> None:
        self._store = FaceEmbeddingStore(settings.face_store_path)
        self._face_app = self._init_model()

    def _init_model(self) -> FaceAnalysis:
        providers = get_available_providers()
        if "CUDAExecutionProvider" in providers:
            ctx_id = 0
            logger.info("Initializing InsightFace on CUDA provider")
        else:
            ctx_id = -1
            logger.info("CUDA provider unavailable, falling back to CPU for face embeddings")
        app = FaceAnalysis(name="buffalo_l", providers=providers)
        app.prepare(ctx_id=ctx_id, det_size=(640, 640))
        return app

    def _decode_image(self, image_base64: str) -> np.ndarray:
        try:
            frame_bytes = base64.b64decode(image_base64)
            np_arr = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        except Exception as exc:  # pragma: no cover
            raise ValueError("Invalid base64 image payload") from exc
        if frame is None:
            raise ValueError("Unable to decode image")
        return frame

    def _extract_embedding(self, image_base64: str) -> np.ndarray:
        frame = self._decode_image(image_base64)
        faces = self._face_app.get(frame)
        if not faces:
            raise ValueError("No face detected")
        # use the most confident detection
        faces.sort(key=lambda face: float(face.det_score), reverse=True)
        embedding = faces[0].normed_embedding
        if embedding is None:
            raise ValueError("Failed to compute embedding")
        return embedding.astype(np.float32)

    def enroll(self, payload: FaceEnrollRequest) -> FaceEnrollResponse:
        embedding = self._extract_embedding(payload.image_base64)
        profile = self._store.add_profile(payload.user_id, embedding)
        return FaceEnrollResponse(message="Face enrolled", profile=profile)

    def verify(self, payload: FaceVerifyRequest) -> FaceVerifyResponse:
        embedding = self._extract_embedding(payload.image_base64)
        candidates = self._store.find_matches(embedding, top_k=payload.top_k)
        matches: List[FaceMatch] = []
        for profile, score in candidates:
            if score < payload.threshold:
                continue
            user = db.get_user(profile.user_id) if hasattr(db, "get_user") else None  # type: ignore[attr-defined]
            matches.append(
                FaceMatch(
                    user_id=profile.user_id,
                    score=score,
                    owner_name=getattr(user, "name", None),
                    owner_phone=getattr(user, "phone", None),
                    owner_affiliation=getattr(user, "programme", None),
                )
            )
        return FaceVerifyResponse(matches=matches)

    def list_profiles(self) -> List[UserFace]:
        return self._store.list_profiles()


face_recognition_service = FaceRecognitionService()
