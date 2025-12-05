from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_name: str = "SmartGate LPR"
    environment: str = "local"
    backend_version: str = "0.2.0"
    api_prefix: str = "/api"
    mock_inference: bool = False
    supabase_url: str = "https://your-project.supabase.co"
    supabase_key: str = "SUPABASE_SERVICE_ROLE_KEY"
    use_supabase: bool = True
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 60
    jwt_secret_key: str = "dev-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    allowed_origins: List[AnyHttpUrl] = [
        AnyHttpUrl("http://localhost:5173"),
        AnyHttpUrl("http://127.0.0.1:5173"),
        AnyHttpUrl("http://localhost:5175"),
        AnyHttpUrl("http://127.0.0.1:5175"),
        AnyHttpUrl("http://localhost:5280"),
        AnyHttpUrl("http://127.0.0.1:5280"),
        AnyHttpUrl("http://localhost"),
        AnyHttpUrl("http://127.0.0.1"),
    ]
    base_guest_rate: float = 2.5
    per_minute_guest_rate: float = 0.75
    yolo_weights_path: str = "models/yolov8n-license.pt"
    yolo_device: str = "auto"
    yolo_max_side: int = 1280
    yolo_conf_threshold: float = 0.45
    yolo_plate_classes: List[int] = []
    ocr_languages: List[str] = ["en"]
    ocr_crop_margin: float = 0.08
    lpr_frame_cache_ms: int = 600
    face_store_path: str = "app/data/face_store.json"
    touchngo_base_url: str = "https://sandbox.touchngo.com.my/mock"
    touchngo_api_key: str = "demo-key"
    touchngo_merchant_id: str = "SMARTGATE"
    touchngo_terminal_id: str = "SG-DEMO-01"
    touchngo_mock_mode: bool = True
    currency_code: str = "MYR"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
