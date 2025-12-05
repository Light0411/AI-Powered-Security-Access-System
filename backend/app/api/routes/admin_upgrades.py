from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas import RoleUpgradeDecision, RoleUpgradeRequest
from app.services.datastore import db

router = APIRouter()


@router.get("", response_model=list[RoleUpgradeRequest])
def list_role_upgrades(status: str | None = Query(default=None)) -> list[RoleUpgradeRequest]:
    if status and status not in {"pending", "approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid status filter")
    return db.list_role_upgrades(status=status)


@router.post("/{request_id}/decision", response_model=RoleUpgradeRequest)
def review_role_upgrade(request_id: str, payload: RoleUpgradeDecision) -> RoleUpgradeRequest:
    try:
        return db.review_role_upgrade(request_id, payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Role upgrade request not found")
