"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings sourced from .env or the process environment."""

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    openai_api_key: str
    gpt_model: str = "gpt-4o-mini"
    site_url: str = "http://localhost:3000"

    # CodeBERT validation layer — reviews GPT bug predictions.
    hf_token: str | None = None
    codebert_model_path: str = "aidencary/codepulse-codebert"
    # Optional explicit buggy-class index override. Use when model label
    # metadata is ambiguous (for example LABEL_0/LABEL_1 placeholders).
    codebert_buggy_index: int | None = None
    codebert_flag_threshold: float = 0.45
    # Number of lines of context to include above and below the bug line when
    # scoring with CodeBERT. 0 = single line only (original training window).
    codebert_context_window: int = 1
    # Contrast mapping spreads close confidence values apart while preserving
    # ordering. Helps when model outputs are compressed.
    codebert_confidence_contrast_strength: float = 2.5
    codebert_confidence_contrast_blend: float = 0.4

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
