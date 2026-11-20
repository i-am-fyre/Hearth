from datetime import datetime, timedelta, timezone
from typing import Any, Union

import bcrypt
import jwt

from app.core.config import settings

ALGORITHM = "HS256"

# bcrypt only looks at the first 72 bytes of its input. passlib, which created
# Hearth's existing hashes, truncated longer passwords silently; bcrypt>=5 raises
# instead. Truncating here keeps those hashes verifiable and avoids a 500 on long
# passwords.
_BCRYPT_MAX_BYTES = 72


def _bcrypt_input(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta | None = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a login token. Raises ``jwt.InvalidTokenError`` if it is not valid."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_bcrypt_input(plain_password), hashed_password.encode("utf-8"))
    except ValueError:
        # Malformed or non-bcrypt hash.
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(_bcrypt_input(password), bcrypt.gensalt()).decode("utf-8")
