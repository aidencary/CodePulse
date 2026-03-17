"""Supabase client initialization using the service role key."""

from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    """Return a cached Supabase client authenticated with the service role key.

    Uses the service role key so inserts/updates bypass RLS.
    Never expose this client or key to the frontend.
    """
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
