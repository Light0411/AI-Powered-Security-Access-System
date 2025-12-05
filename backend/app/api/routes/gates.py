from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas import AccessEvent
from app.services.datastore import db

router = APIRouter()


@router.get("", response_model=list[AccessEvent])
@router.get("/", response_model=list[AccessEvent])
def list_access_events(limit: int = Query(default=50, le=200)) -> list[AccessEvent]:
    return db.list_access_events(limit=limit)
