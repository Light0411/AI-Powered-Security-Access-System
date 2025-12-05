from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas import (
    GuestPaymentRequest,
    GuestRateResponse,
    GuestRateUpdate,
    GuestSession,
    GuestSessionClose,
    GuestSessionCreate,
    Payment,
)
from app.services.datastore import db

router = APIRouter()


@router.get("/sessions", response_model=list[GuestSession])
def list_guest_sessions() -> list[GuestSession]:
    return db.list_guest_sessions()


@router.post("/session/open", response_model=GuestSession, status_code=status.HTTP_201_CREATED)
def open_guest_session(payload: GuestSessionCreate) -> GuestSession:
    return db.open_guest_session(payload)


@router.post("/session/close", response_model=GuestSession)
def close_guest_session(payload: GuestSessionClose) -> GuestSession:
    try:
        return db.close_guest_session(payload.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Guest session not found")


@router.post("/session/pay", response_model=Payment)
def pay_guest_session(payload: GuestPaymentRequest) -> Payment:
    try:
        return db.pay_guest_session(payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Guest session not found")


@router.get("/rate", response_model=GuestRateResponse)
def get_guest_rate() -> GuestRateResponse:
    return db.get_guest_rate()


@router.put("/rate", response_model=GuestRateResponse)
def update_guest_rate(payload: GuestRateUpdate) -> GuestRateResponse:
    return db.update_guest_rate(payload)
