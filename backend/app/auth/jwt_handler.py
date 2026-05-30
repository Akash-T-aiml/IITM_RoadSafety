"""
SmartRescue AI — JWT Token Handler
Create and decode internal JWT tokens for API authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def create_access_token(
    data: Dict[str, Any],
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT token with user data and role.
    """
    settings = get_settings()

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    )

    to_encode.update({
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "smartrescue-ai",
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    logger.info(
        "JWT created",
        extra={"sub": data.get("sub"), "role": role}
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    Raises HTTPException 401 if invalid or expired.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require_exp": True},
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
