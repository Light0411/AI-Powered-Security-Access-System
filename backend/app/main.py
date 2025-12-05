from __future__ import annotations

import asyncio

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from loguru import logger

from app.core.config import settings
from app.api import api_router
from app.services.vision import vision_pipeline

app = FastAPI(title=settings.project_name, version=settings.backend_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        *(str(origin).rstrip("/") for origin in settings.allowed_origins),
        *(str(origin) for origin in settings.allowed_origins),
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "version": settings.backend_version}


@app.api_route("/", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def redirect_root() -> RedirectResponse:
    return RedirectResponse(url=settings.api_prefix + "/health", status_code=307)


@app.on_event("startup")
async def warmup_vision_pipeline() -> None:
    """Load YOLO/EasyOCR weights ahead of the first inference request."""
    if settings.mock_inference:
        logger.warning("MOCK_INFERENCE flag ignored; forcing real pipeline warmup")
    logger.info("Warming up vision pipeline (YOLO/EasyOCR)")
    ready = await asyncio.to_thread(vision_pipeline.available)
    if ready:
        logger.info("Vision pipeline ready for requests")
    else:
        logger.warning("Vision pipeline unavailable after warmup; falling back to mock detections")


if __name__ == "__main__":  # pragma: no cover - convenience entrypoint
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
