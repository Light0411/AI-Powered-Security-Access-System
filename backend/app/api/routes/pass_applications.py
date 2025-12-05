from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas import PassApplication, PassApplicationDecision
from app.services.datastore import db

router = APIRouter()


@router.get("", response_model=list[PassApplication])
def list_pass_applications(status: str | None = Query(default=None)) -> list[PassApplication]:
    if status and status not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid status filter")
    return db.list_pass_applications(status=status)


@router.post("/{application_id}/decision", response_model=PassApplication)
def review_pass_application(application_id: str, payload: PassApplicationDecision) -> PassApplication:
    try:
        return db.review_pass_application(application_id, payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Pass application not found")
