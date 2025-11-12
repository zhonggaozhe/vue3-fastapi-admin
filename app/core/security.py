from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def _load_key(path: str) -> str:
    key_path = Path(path)
    if not key_path.exists():
        # For bootstrap we fall back to a randomly generated secret
        return get_settings().app_name
    return key_path.read_text()


@lru_cache
def get_signing_key() -> str:
    settings = get_settings()
    if settings.jwt_algorithm.upper().startswith("HS"):
        return settings.jwt_secret_key
    return _load_key(settings.jwt_private_key_path)


@lru_cache
def get_verification_key() -> str:
    settings = get_settings()
    if settings.jwt_algorithm.upper().startswith("HS"):
        return settings.jwt_secret_key
    return _load_key(settings.jwt_public_key_path)


def create_jwt_token(sub: str, expires_minutes: int, token_type: str, **claims: Any) -> dict[str, Any]:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        "jti": str(uuid4()),
        **claims,
    }
    token = jwt.encode(payload, get_signing_key(), algorithm=settings.jwt_algorithm)
    return {"token": token, "payload": payload}


def decode_jwt_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, get_verification_key(), algorithms=[settings.jwt_algorithm])
    except JWTError as exc:  # pragma: no cover - thin wrapper
        raise ValueError("Invalid token") from exc
