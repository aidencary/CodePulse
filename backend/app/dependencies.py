"""FastAPI dependency functions for authentication."""

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.config import Settings, get_settings

_ALGORITHM = "HS256"


def get_current_user(
    authorization: str = Header(..., description="Bearer <supabase_jwt>"),
    settings: Settings = Depends(get_settings),
) -> str:
    """Validate the Supabase JWT and return the authenticated user_id.

    Args:
        authorization: Raw Authorization header value (``Bearer <token>``).
        settings: Application settings injected via FastAPI dependency.

    Returns:
        The ``sub`` claim from the verified JWT, which is the Supabase user UUID.

    Raises:
        HTTPException: 401 if the token is missing, malformed, or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not authorization.startswith("Bearer "):
        raise credentials_exception

    token = authorization[len("Bearer "):]

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=[_ALGORITHM],
            audience="authenticated",
        )

        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return user_id

