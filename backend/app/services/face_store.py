from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import List, Sequence
from uuid import uuid4

import numpy as np

from app.schemas import UserFace


@dataclass
class FaceProfile:
    id: str
    user_id: str
    embedding: List[float]
    captured_at: str

    def to_schema(self) -> UserFace:
        return UserFace(
            id=self.id,
            user_id=self.user_id,
            embedding=self.embedding,
            captured_at=datetime.fromisoformat(self.captured_at),
        )


class FaceEmbeddingStore:
    """Tiny JSON-backed store for face embeddings."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._lock = Lock()
        self._profiles: List[FaceProfile] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            self._persist()
            return
        try:
            with open(self._path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
                self._profiles = [FaceProfile(**entry) for entry in raw]
        except (json.JSONDecodeError, OSError, TypeError):
            self._profiles = []

    def _persist(self) -> None:
        data = [asdict(profile) for profile in self._profiles]
        with open(self._path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

    def list_profiles(self) -> List[UserFace]:
        return [profile.to_schema() for profile in self._profiles]

    def add_profile(self, user_id: str, embedding: Sequence[float]) -> UserFace:
        with self._lock:
            profile = FaceProfile(
                id=f"FACE-{uuid4().hex[:8].upper()}",
                user_id=user_id,
                embedding=[float(value) for value in embedding],
                captured_at=datetime.now(timezone.utc).isoformat(),
            )
            self._profiles.append(profile)
            self._persist()
            return profile.to_schema()

    def find_matches(self, embedding: np.ndarray, top_k: int = 3) -> List[tuple[UserFace, float]]:
        if not self._profiles:
            return []
        targets = np.array([profile.embedding for profile in self._profiles], dtype=np.float32)
        embedding = embedding.astype(np.float32)
        embedding /= np.linalg.norm(embedding) + 1e-8
        targets /= np.linalg.norm(targets, axis=1, keepdims=True) + 1e-8
        scores = np.dot(targets, embedding)
        ranked_indices = np.argsort(scores)[::-1][:top_k]
        return [(self._profiles[idx].to_schema(), float(scores[idx])) for idx in ranked_indices]
