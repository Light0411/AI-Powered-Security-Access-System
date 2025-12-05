from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas import (
    ClientGuestPaymentRequest,
    ClientRegistrationRequest,
    ClientRegistrationResponse,
    ClientSummary,
    ClientWalletActivity,
    GuestSessionLookupResponse,
    Notification,
    NotificationAck,
    ParkingOverview,
    Pass,
    Payment,
    RoleUpgradeRequest,
    RoleUpgradeSubmit,
    WalletTopUpRequest,
)
from app.services.datastore import db

router = APIRouter()


@router.post("/register", response_model=ClientRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_client(payload: ClientRegistrationRequest) -> ClientRegistrationResponse:
    try:
        return db.register_client(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/summary/{user_id}", response_model=ClientSummary)
def fetch_client_summary(user_id: str) -> ClientSummary:
    try:
        return db.get_client_summary(user_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/wallet/{user_id}", response_model=ClientWalletActivity)
def fetch_wallet_activity(user_id: str) -> ClientWalletActivity:
    try:
        return db.get_wallet_activity(user_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.post("/wallet/{user_id}/top-up", response_model=ClientWalletActivity)
def wallet_top_up(user_id: str, payload: WalletTopUpRequest) -> ClientWalletActivity:
    try:
        return db.wallet_top_up(user_id, payload)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/role-upgrade/{user_id}", response_model=RoleUpgradeRequest, status_code=status.HTTP_201_CREATED)
def submit_role_upgrade(user_id: str, payload: RoleUpgradeSubmit) -> RoleUpgradeRequest:
    try:
        return db.submit_role_upgrade(user_id, payload)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/guest/lookup", response_model=GuestSessionLookupResponse)
def lookup_guest_session(
    session_id: str | None = Query(default=None),
    plate_text: str | None = Query(default=None),
) -> GuestSessionLookupResponse:
    if not session_id and not plate_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide session_id or plate_text")
    try:
        return db.lookup_guest_session(session_id=session_id, plate_text=plate_text)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guest session not found")


@router.post("/guest/pay", response_model=Payment)
def pay_guest_session(payload: ClientGuestPaymentRequest) -> Payment:
    try:
        return db.client_pay_guest_session(payload)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guest session not found")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/parking", response_model=ParkingOverview)
def get_parking_overview() -> ParkingOverview:
    return db.get_parking_overview()


@router.get("/notifications/{user_id}", response_model=list[Notification])
def list_notifications(user_id: str) -> list[Notification]:
    try:
        return db.list_notifications(user_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="User not found")


@router.post("/notifications/{user_id}/ack", response_model=Notification)
def acknowledge_notification(user_id: str, payload: NotificationAck) -> Notification:
    try:
        return db.acknowledge_notification(user_id, payload.notification_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Notification not found")
@router.post("/pass/{pass_id}/pay", response_model=Pass)
def pay_pass(pass_id: str, user_id: str = Query(...)) -> Pass:
    try:
        return db.pay_pass_invoice(user_id, pass_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pass not found")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
