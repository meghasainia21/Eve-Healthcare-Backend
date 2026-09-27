"""
Password hashing and JWT helpers.

Kept deliberately small and framework-agnostic so it's easy to unit test
and easy to explain live: "we hash with bcrypt, we sign a JWT with a
secret key and an expiry, and we verify both on every protected request."
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """Create a signed JWT whose `sub` claim is the user id (as a string)."""
    expire_delta = timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire_at = datetime.now(timezone.utc) + expire_delta
    to_encode: dict[str, Any] = {"sub": subject, "exp": expire_at}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


class TokenError(Exception):
    """Raised for any invalid/expired/malformed JWT."""


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        raise TokenError("Could not validate credentials") from exc
