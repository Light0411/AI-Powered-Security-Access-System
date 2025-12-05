from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from loguru import logger

from app.core.config import settings


@dataclass(frozen=True)
class TouchNGoChargeResult:
    transaction_id: str
    status: str
    amount_rm: float
    currency: str
    processor: str = "touchngo"


class TouchNGoGateway:
    """Minimal Touch 'n Go eWallet client with optional mock mode."""

    def __init__(self) -> None:
        self._base_url = settings.touchngo_base_url.rstrip("/")
        self._api_key = settings.touchngo_api_key
        self._merchant_id = settings.touchngo_merchant_id
        self._terminal_id = settings.touchngo_terminal_id
        self._mock_mode = settings.touchngo_mock_mode
        self._currency = settings.currency_code

    def charge(
        self,
        *,
        amount_rm: float,
        reference: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TouchNGoChargeResult:
        payload = {
            "amount": round(amount_rm, 2),
            "currency": self._currency,
            "reference": reference,
            "description": description,
            "merchant_id": self._merchant_id,
            "terminal_id": self._terminal_id,
            "metadata": metadata or {},
        }
        if self._mock_mode or amount_rm <= 0:
            txn_id = self._mock_reference()
            logger.info("Touch 'n Go mock payment {} RM{} [{}]", reference, payload["amount"], txn_id)
            return TouchNGoChargeResult(
                transaction_id=txn_id,
                status="succeeded",
                amount_rm=payload["amount"],
                currency=self._currency,
            )
        try:
            response = httpx.post(
                f"{self._base_url}/charges",
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            txn_id = data.get("transaction_id") or data.get("txnId") or self._mock_reference()
            status = data.get("status", "succeeded")
            logger.info("Touch 'n Go charge {} completed with {}", txn_id, status)
            return TouchNGoChargeResult(
                transaction_id=txn_id,
                status=status,
                amount_rm=payload["amount"],
                currency=data.get("currency", self._currency),
            )
        except httpx.HTTPError as exc:  # pragma: no cover - depends on network
            logger.opt(exception=exc).error("Touch 'n Go API failure for {}", reference)
            raise ValueError("Touch 'n Go payment failed") from exc

    def charge_pass(self, *, user_id: str, plan_type: str, amount_rm: float) -> TouchNGoChargeResult:
        return self.charge(
            amount_rm=amount_rm,
            reference=f"pass:{user_id}",
            description=f"{plan_type} pass",
            metadata={"user_id": user_id, "plan_type": plan_type},
        )

    def charge_guest(self, *, session_id: str, amount_rm: float, plate_text: str) -> TouchNGoChargeResult:
        return self.charge(
            amount_rm=amount_rm,
            reference=f"guest:{session_id}",
            description="Guest parking",
            metadata={"session_id": session_id, "plate_text": plate_text},
        )

    def charge_wallet_top_up(self, *, user_id: str, amount_rm: float) -> TouchNGoChargeResult:
        return self.charge(
            amount_rm=amount_rm,
            reference=f"wallet:{user_id}",
            description="Wallet top-up",
            metadata={"user_id": user_id},
        )

    @staticmethod
    def _mock_reference() -> str:
        return f"TNG-{uuid.uuid4().hex[:10].upper()}"


touchngo_gateway = TouchNGoGateway()

__all__ = ["touchngo_gateway", "TouchNGoChargeResult"]
