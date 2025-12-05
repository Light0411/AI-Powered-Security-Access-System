from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from loguru import logger
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings


class CacheKeys:
    """Utility helpers to keep Redis key naming consistent."""

    namespace = "smartgate"

    @classmethod
    def access_events(cls) -> str:
        return f"{cls.namespace}:access_events"

    @classmethod
    def guest_session(cls, plate_text: str) -> str:
        return f"{cls.namespace}:guest_session:{plate_text.upper()}"

    @classmethod
    def inference_snapshot(cls, gate: str) -> str:
        return f"{cls.namespace}:inference:{gate}"

    @classmethod
    def rate_limit(cls, gate: str) -> str:
        return f"{cls.namespace}:ratelimit:{gate}"


class RedisCache:
    def __init__(self) -> None:
        self._ttl = settings.redis_cache_ttl
        self._client = Redis.from_url(settings.redis_url, decode_responses=True)

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------
    def set_json(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        try:
            payload = json.dumps(value, default=str)
            self._client.setex(key, ttl or self._ttl, payload)
        except RedisError as exc:  # pragma: no cover - best effort cache
            logger.opt(exception=exc).warning("Redis set_json failed for key {}", key)

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            raw = self._client.get(key)
            return json.loads(raw) if raw else None
        except RedisError as exc:  # pragma: no cover
            logger.opt(exception=exc).warning("Redis get_json failed for key {}", key)
            return None

    def delete(self, key: str) -> None:
        try:
            self._client.delete(key)
        except RedisError as exc:  # pragma: no cover
            logger.opt(exception=exc).warning("Redis delete failed for key {}", key)

    def push_json(self, key: str, value: Dict[str, Any], max_length: int = 50) -> None:
        try:
            payload = json.dumps(value, default=str)
            pipe = self._client.pipeline()
            pipe.lpush(key, payload)
            pipe.ltrim(key, 0, max_length - 1)
            pipe.expire(key, self._ttl)
            pipe.execute()
        except RedisError as exc:  # pragma: no cover
            logger.opt(exception=exc).warning("Redis push_json failed for key {}", key)

    def list_json(self, key: str, limit: int) -> List[Dict[str, Any]]:
        try:
            entries = self._client.lrange(key, 0, max(0, limit - 1))
            return [json.loads(entry) for entry in entries]
        except RedisError as exc:  # pragma: no cover
            logger.opt(exception=exc).warning("Redis list_json failed for key {}", key)
            return []

    # ------------------------------------------------------------------
    # Rate limiting helpers
    # ------------------------------------------------------------------
    def hit_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        """Return True if the caller exceeded the allowed hits within window."""
        try:
            value = self._client.incr(key)
            if value == 1:
                self._client.expire(key, window_seconds)
            return value > limit
        except RedisError as exc:  # pragma: no cover
            logger.opt(exception=exc).warning("Redis rate_limit failed for key {}", key)
            return False


redis_cache = RedisCache()

__all__ = ["redis_cache", "CacheKeys"]
