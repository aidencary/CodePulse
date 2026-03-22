"""FastAPI dependency functions for authentication."""

from functools import lru_cache

import httpx
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.config import Settings, get_settings


@lru_cache(maxsize=4)
def _fetch_jwks(supabase_url: str) -> dict:
    """Fetch and cache the JWKS from Supabase's well-known endpoint.

    Args:
        supabase_url: The Supabase project URL used to build the JWKS URI.

    Returns:
        The parsed JWKS JSON as a dict.
    """
    url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
    response = httpx.get(url, timeout=5.0)
    response.raise_for_status()
    return response.json()


def get_current_user(
    authorization: str = Header(..., description="Bearer <supabase_jwt>"),
    settings: Settings = Depends(get_settings),
) -> str:
    """Validate the Supabase JWT and return the authenticated user_id.

    Supports both HS256 (legacy) and ES256 (current Supabase default) tokens.
    ES256 tokens are verified against the project's JWKS public keys.

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

    token = authorization[len("Bearer ") :]

    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        raise credentials_exception

    alg = header.get("alg", "HS256")

    if alg == "ES256":
        # Verify using the Supabase JWKS public key.
        kid = header.get("kid")
        try:
            jwks = _fetch_jwks(settings.supabase_url)
        except Exception:
            raise credentials_exception
        verify_key = next(
            (k for k in jwks.get("keys", []) if k.get("kid") == kid),
            None,
        )
        if verify_key is None:
            raise credentials_exception
        algorithms = ["ES256"]
    else:
        # Legacy HS256 — use the JWT secret directly.
        verify_key = settings.supabase_jwt_secret
        algorithms = ["HS256"]

    try:
        payload = jwt.decode(
            token,
            verify_key,
            algorithms=algorithms,
            audience="authenticated",
        )

        if payload.get("iss") != f"{settings.supabase_url}/auth/v1":
            raise credentials_exception

        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return user_id
