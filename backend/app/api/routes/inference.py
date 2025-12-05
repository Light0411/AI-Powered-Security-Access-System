from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.schemas import InferenceRequest, InferenceResponse
from app.services.cache import CacheKeys, redis_cache
from app.services.inference import inference_service

router = APIRouter()

RATE_LIMIT_REQUESTS = 5
RATE_LIMIT_WINDOW_SECONDS = 3


@router.options("", include_in_schema=False)
@router.options("/", include_in_schema=False)
def options_inference() -> Response:
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )


@router.post("", response_model=InferenceResponse)
@router.post("/", response_model=InferenceResponse)
async def run_inference(payload: InferenceRequest) -> InferenceResponse:
    limiter_key = CacheKeys.rate_limit(payload.gate)
    if redis_cache.hit_rate_limit(limiter_key, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Gate capture throttled. Please wait a few seconds.",
        )
    return await inference_service.infer(payload)
