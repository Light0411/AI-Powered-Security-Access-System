from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from app.core.config import settings
from app.core.constants import GATE_MIN_ROLE, ROLE_WEIGHTS
from app.schemas import (
    AccessDecision,
    AccessEventBase,
    GuestSessionCreate,
    InferenceRequest,
    InferenceResponse,
    ParkingEventRequest,
)

from .cache import CacheKeys, redis_cache
from .datastore import db
from .vision import VisionDetection, vision_pipeline


@dataclass
class PlateDetection:
    plate_text: str
    confidence: float


class InferenceService:
    """Encapsulates the YOLO → OCR pipeline (mocked for laptop demo)."""

    def __init__(self, mock_mode: bool | None = None) -> None:
        if mock_mode is None and settings.mock_inference:
            logger.warning("MOCK_INFERENCE flag ignored; forcing real pipeline mode")
        self.mock_mode = False if mock_mode is None else mock_mode

    async def infer(self, request: InferenceRequest) -> InferenceResponse:
        detection = await self._detect_plate_async(request)
        decision = await asyncio.to_thread(self._decide, detection, request.gate)
        event_payload = AccessEventBase(
            plate_text=decision.plate_text,
            confidence=decision.confidence,
            decision=decision.decision,
            role=decision.role,
            reason=decision.reason,
            gate=decision.gate,
            snapshot_url=None,
        )
        event = await asyncio.to_thread(db.add_access_event, event_payload)
        redis_cache.push_json(CacheKeys.access_events(), event.model_dump(mode="json"), max_length=100)
        redis_cache.set_json(CacheKeys.inference_snapshot(decision.gate), decision.model_dump(mode="json"))
        await asyncio.to_thread(self._update_parking_state, decision)
        return InferenceResponse(decision=decision, event=event)

    async def _detect_plate_async(self, request: InferenceRequest) -> PlateDetection:
        if self.mock_mode:
            return self._detect_plate(request)
        return await asyncio.to_thread(self._detect_plate, request)

    def _detect_plate(self, request: InferenceRequest) -> PlateDetection:
        if request.plate_override:
            return PlateDetection(plate_text=request.plate_override.upper(), confidence=0.99)

        if request.image_base64 and not self.mock_mode:
            vision_result = self._real_inference(request.image_base64)
            if vision_result:
                return vision_result

        if self.mock_mode:
            demo_pool = [vehicle.plate_text for vehicle in db.list_vehicles()]
            demo_pool.append("VISITX")
            plate = random.choice(demo_pool)
            confidence = round(random.uniform(0.78, 0.94), 2)
            return PlateDetection(plate_text=plate, confidence=confidence)

        logger.warning("Vision pipeline returned no detection; marking UNKNOWN plate")
        return PlateDetection(plate_text="UNKNOWN", confidence=0.0)

    def _real_inference(self, frame_base64: str) -> Optional[PlateDetection]:
        if not vision_pipeline.available():
            return None
        result: Optional[VisionDetection] = vision_pipeline.detect_from_base64(frame_base64)
        if result:
            return PlateDetection(plate_text=result.plate_text, confidence=result.confidence)
        return None

    def _decide(self, detection: PlateDetection, gate: str) -> AccessDecision:
        gate_slug, target_role = self._resolve_gate(gate)
        user, _ = db.find_user_by_plate(detection.plate_text)
        required_weight = ROLE_WEIGHTS[target_role]

        owner_fields: dict[str, Optional[str | datetime]] = {
            "owner_name": None,
            "owner_phone": None,
            "owner_affiliation": None,
            "pass_valid_to": None,
        }

        if not user:
            if required_weight > ROLE_WEIGHTS["guest"]:
                return AccessDecision(
                    plate_text=detection.plate_text,
                    confidence=detection.confidence,
                    decision="DENY",
                    role="guest",
                    reason=f"Unregistered plate - {gate_slug} requires {target_role}+",
                    gate=gate_slug,
                    **owner_fields,
                )
            self._ensure_guest_session(detection.plate_text)
            return AccessDecision(
                plate_text=detection.plate_text,
                confidence=detection.confidence,
                decision="GUEST",
                role="guest",
                reason="Unregistered plate, guest flow started",
                gate=gate_slug,
                **owner_fields,
            )

        owner_fields.update(
            {
                "owner_name": user.name,
                "owner_phone": user.phone,
                "owner_affiliation": user.programme,
            }
        )

        latest_pass = db.get_latest_pass(user.id)
        if latest_pass and not latest_pass.is_paid:
            return AccessDecision(
                plate_text=detection.plate_text,
                confidence=detection.confidence,
                decision="DENY",
                role=user.role,
                reason="Pass unpaid - settle wallet invoice",
                gate=gate_slug,
                **owner_fields,
            )
        if latest_pass:
            owner_fields["pass_valid_to"] = latest_pass.valid_to

        if latest_pass is None:
            return AccessDecision(
                plate_text=detection.plate_text,
                confidence=detection.confidence,
                decision="DENY",
                role=user.role,
                reason="No pass on file",
                gate=gate_slug,
                **owner_fields,
            )

        if latest_pass.valid_to <= datetime.now(timezone.utc):
            expiry = latest_pass.valid_to.date().isoformat()
            return AccessDecision(
                plate_text=detection.plate_text,
                confidence=detection.confidence,
                decision="DENY",
                role=user.role,
                reason=f"Pass expired ({expiry})",
                gate=gate_slug,
                **owner_fields,
            )

        role_weight = ROLE_WEIGHTS.get(user.role, 0)
        if role_weight >= required_weight:
            return AccessDecision(
                plate_text=detection.plate_text,
                confidence=detection.confidence,
                decision="ALLOW",
                role=user.role,
                reason=f"{user.role.title()} role >= {target_role} gate threshold",
                gate=gate_slug,
                **owner_fields,
            )

        return AccessDecision(
            plate_text=detection.plate_text,
            confidence=detection.confidence,
            decision="DENY",
            role=user.role,
            reason=f"{user.role.title()} role below {gate_slug} requirement",
            gate=gate_slug,
            **owner_fields,
        )

    def _resolve_gate(self, gate: Optional[str]) -> tuple[str, str]:
        slug = (gate or "outer").lower()
        gate_obj = db.get_gate_by_slug(slug)
        if gate_obj and gate_obj.is_active:
            return gate_obj.slug, gate_obj.min_role
        return slug, GATE_MIN_ROLE.get(slug, "guest")

    def _ensure_guest_session(self, plate_text: str) -> None:
        existing = db.find_guest_session_by_plate(plate_text, status="open")
        if existing:
            return
        db.open_guest_session(payload=GuestSessionCreate(plate_text=plate_text))

    def _update_parking_state(self, decision: AccessDecision) -> None:
        if decision.decision not in ("ALLOW", "GUEST"):
            return
        gate = db.get_gate_by_slug(decision.gate)
        if not gate or not gate.parking_venue_id or not gate.parking_direction:
            return
        try:
            db.record_parking_event(
                ParkingEventRequest(venue_id=gate.parking_venue_id, direction=gate.parking_direction)
            )
        except Exception as exc:  # pragma: no cover - defensive logging only
            logger.warning("Failed to update parking for gate {}: {}", gate.slug, exc)


inference_service = InferenceService()
