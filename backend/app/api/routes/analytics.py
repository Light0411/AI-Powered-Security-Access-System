from __future__ import annotations

from fastapi import APIRouter

from app.schemas import AnalyticsResponse
from app.services.analytics import build_analytics

router = APIRouter()


@router.get("/mock", response_model=AnalyticsResponse)
def get_mock_analytics() -> AnalyticsResponse:
    return build_analytics()
