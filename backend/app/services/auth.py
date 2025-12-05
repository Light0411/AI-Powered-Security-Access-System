from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self) -> None:
        self.secret = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expire_minutes = settings.jwt_expire_minutes

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, password: str, hashed: str) -> bool:
        return pwd_context.verify(password, hashed)

    def create_token(self, subject: Dict[str, Any]) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.expire_minutes)
        payload = {"sub": subject, "exp": expire}
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        data = jwt.decode(token, self.secret, algorithms=[self.algorithm])
        return data.get("sub", {})


auth_service = AuthService()
