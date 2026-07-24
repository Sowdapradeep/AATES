from datetime import UTC, datetime, timedelta
from typing import Any
from jose import jwt, JWTError
from core.config import settings

def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Signs and encodes a JWT access token with expiration time."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC).replace(tzinfo=None) + expires_delta
    else:
        expire = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=settings.security.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.security.secret_key, algorithm=settings.security.algorithm)

def create_refresh_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Signs and encodes a JWT refresh token with extended expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC).replace(tzinfo=None) + expires_delta
    else:
        expire = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=settings.security.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.security.secret_key, algorithm=settings.security.algorithm)

def decode_token(token: str) -> dict[str, Any] | None:
    """Decodes and validates a signed JWT token signature."""
    try:
        return jwt.decode(token, settings.security.secret_key, algorithms=[settings.security.algorithm])
    except JWTError:
        return None
