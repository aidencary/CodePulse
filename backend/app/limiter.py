"""Per-user rate limiter used to protect expensive endpoints.

The /analyze endpoint calls OpenAI and runs CodeBERT inference on every
request, so it is the main cost/DoS surface in the API. We key limits on
the Authorization header (unique per user session) with a fallback to
the remote address for any unauthenticated traffic that slips through.
"""

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _user_key(request: Request) -> str:
    """Return a rate-limit key derived from the bearer token or client IP."""
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[len("Bearer ") :].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_user_key)
