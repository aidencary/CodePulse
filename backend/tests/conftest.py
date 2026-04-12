"""Shared pytest fixtures for the backend test suite.

Notably: prevent the CodeBERT validator from reaching out to HuggingFace
during tests. Loading the real model would download ~500 MB and require
a valid HF_TOKEN — neither is appropriate for unit tests.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services import codebert_validator


@pytest.fixture(autouse=True)
def _disable_codebert_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """No-op the CodeBERT loader and clear any previously-loaded model.

    With ``_model`` and ``_tokenizer`` both None, ``validate_predictions``
    short-circuits and returns its input unchanged — the safe-fallback
    path exercised in production when model load fails.

    Individual tests that want to exercise the inference path can assign
    fakes to ``codebert_validator._model`` / ``_tokenizer`` directly; this
    fixture's monkeypatch is scoped per-test and will restore them.
    """
    monkeypatch.setattr(codebert_validator, "_model", None)
    monkeypatch.setattr(codebert_validator, "_tokenizer", None)
    monkeypatch.setattr(codebert_validator, "load_model", lambda: None)
    # CI has no .env, so constructing real Settings would fail validation.
    # Stub get_settings with the threshold the validator actually reads.
    monkeypatch.setattr(
        codebert_validator,
        "get_settings",
        lambda: SimpleNamespace(
            codebert_flag_threshold=0.3,
            codebert_context_window=1,
        ),
    )
    # The inference cache is module-global — clear it so fake-model results
    # from one test never leak into another.
    codebert_validator._score_cache.clear()

    # Also patch the symbol imported into app.main so the FastAPI lifespan
    # hook is a no-op regardless of import timing.
    try:
        from app import main as app_main

        monkeypatch.setattr(app_main, "load_codebert", lambda: None)
    except ImportError:
        pass
