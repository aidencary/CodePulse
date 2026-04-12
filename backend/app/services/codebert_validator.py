"""CodeBERT validation layer — post-processes GPT bug predictions.

Loads a fine-tuned CodeBERT binary classifier once at startup and scores
each GPT-predicted bug. The "buggy" label index is read from the model's
``config.label2id`` at load time, so either label order works and a later
retrain won't require a code change. Predictions whose P(buggy) falls
below ``codebert_flag_threshold`` are marked ``flagged`` so downstream
scoring can skip their penalty.

Safe-fallback everywhere: if the model fails to load (e.g. OOM on free-tier
hosting) or inference raises, input bugs are returned untouched and the
pipeline degrades to pre-CodeBERT behavior.
"""

from __future__ import annotations

import asyncio
import logging
import re
from threading import Lock
from typing import Any

from app.config import get_settings
from app.models.analysis import PredictedBug

logger = logging.getLogger(__name__)

_model: Any = None
_tokenizer: Any = None
_lock = Lock()

# Index of the "buggy" class in the model's output logits. Resolved from
# ``model.config.label2id`` in ``load_model``; defaults to 0 because the
# current ``aidencary/codepulse-codebert`` checkpoint ships with placeholder
# ``LABEL_0``/``LABEL_1`` names and label 0 is empirically the buggy class.
# A retrain that sets ``id2label={0: "clean", 1: "buggy"}`` will flip this
# automatically with no code change required.
_buggy_index: int = 0

# Bounded cache of snippet → P(buggy). Inference is deterministic in eval
# mode so repeated snippets (re-runs, similar code) are free after the first
# hit. Cleared on every new model load via ``load_model``.
_SCORE_CACHE_MAX = 512
_score_cache: dict[str, float] = {}

# Matches Python string literals OR a `#` comment to end of line. Using the
# alternation lets the sub() callback leave string bodies alone and only
# delete real comments — so ``url = "http://x"`` survives but ``x  # hi``
# becomes ``x``. Imperfect for triple-quoted strings, which single-line bug
# snippets essentially never contain.
_COMMENT_RE = re.compile(
    r"""(?P<str>"[^"\\\n]*(?:\\.[^"\\\n]*)*"|'[^'\\\n]*(?:\\.[^'\\\n]*)*')"""
    r"|(?P<cmt>\#[^\n]*)"
)


def _resolve_buggy_index(model: Any) -> int:
    """Inspect ``model.config.label2id`` and return the index of the buggy class.

    Accepts any case-insensitive label matching ``buggy``/``bug``/``positive``
    and returns its id. If the config only exposes ``LABEL_0``/``LABEL_1``
    placeholders (no semantic names), falls back to 0 — the empirically-known
    layout of the current ``aidencary/codepulse-codebert`` checkpoint.
    """
    label2id = getattr(getattr(model, "config", None), "label2id", None) or {}
    for name, idx in label2id.items():
        if str(name).strip().lower() in {"buggy", "bug", "positive", "1"}:
            return int(idx)
    return 0


def load_model() -> None:
    """Load CodeBERT model + tokenizer once. Idempotent; safe to call repeatedly."""
    global _model, _tokenizer, _buggy_index
    with _lock:
        if _model is not None:
            return

        # Imports are local so test suites and pipeline stages that never
        # call load_model() don't pay the transformers/torch import cost.
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        settings = get_settings()
        logger.info("Loading CodeBERT model from %s", settings.codebert_model_path)
        _tokenizer = AutoTokenizer.from_pretrained(
            settings.codebert_model_path, token=settings.hf_token
        )
        _model = AutoModelForSequenceClassification.from_pretrained(
            settings.codebert_model_path, token=settings.hf_token
        )
        _model.eval()
        _buggy_index = _resolve_buggy_index(_model)
        _score_cache.clear()
        logger.info(
            "CodeBERT model loaded. Buggy class index: %d (label2id=%s)",
            _buggy_index,
            getattr(_model.config, "label2id", {}),
        )


def _strip_comments(code: str) -> str:
    """Remove ``# …`` comments while preserving string literals.

    The inline comment on a bug line often leaks the label to the model
    (e.g. ``x.foo()  # null deref here``) which inflates confidence on
    training-like inputs and tanks it on realistic code. Stripping gives
    the classifier a fair look at the code itself.
    """

    def _sub(match: re.Match[str]) -> str:
        if match.group("cmt") is not None:
            return ""
        return match.group("str")

    return _COMMENT_RE.sub(_sub, code)


def _extract_snippet(code: str, line_number: int | None, window: int = 0) -> str:
    """Return the bug line plus ``window`` lines of context above and below.

    Comments are stripped first so a ``# null deref`` annotation on the bug
    line can't leak the label into the model. Remaining lines are joined
    with ``\\n`` and the block's common leading indentation is removed so
    the model sees the code at column 0. Returns an empty string for
    ``None`` line numbers or out-of-range values.
    """
    if line_number is None:
        return ""
    cleaned = _strip_comments(code)
    lines = cleaned.splitlines()
    if not (1 <= line_number <= len(lines)):
        return ""
    start = max(0, line_number - 1 - window)
    end = min(len(lines), line_number + window)
    block = lines[start:end]
    non_blank = [ln for ln in block if ln.strip()]
    if not non_blank:
        return ""
    indent = min(len(ln) - len(ln.lstrip()) for ln in non_blank)
    dedented = [(ln[indent:] if len(ln) >= indent else ln).rstrip() for ln in block]
    # Drop leading/trailing blank lines that fall out of comment stripping.
    while dedented and not dedented[0].strip():
        dedented.pop(0)
    while dedented and not dedented[-1].strip():
        dedented.pop()
    return "\n".join(dedented)


def _score_snippet(snippet: str) -> float:
    """Return P(buggy) for a snippet, hitting the cache when possible.

    Synchronous so it can be handed to ``asyncio.to_thread`` — CPU-bound
    torch inference must not run on the event loop or it stalls other
    requests.
    """
    cached = _score_cache.get(snippet)
    if cached is not None:
        return cached

    import torch
    import torch.nn.functional as F

    inputs = _tokenizer(
        snippet,
        truncation=True,
        padding=True,
        max_length=512,
        return_tensors="pt",
    )
    with torch.no_grad():
        logits = _model(**inputs).logits
    probs = F.softmax(logits, dim=-1)[0]
    p_buggy = float(probs[_buggy_index])

    if len(_score_cache) >= _SCORE_CACHE_MAX:
        # Cheap eviction: drop an arbitrary entry. LRU would need OrderedDict
        # and another lock — not worth it for a best-effort cache.
        _score_cache.pop(next(iter(_score_cache)))
    _score_cache[snippet] = p_buggy
    return p_buggy


async def validate_predictions(
    code: str, predicted_bugs: list[PredictedBug]
) -> list[PredictedBug]:
    """Score each predicted bug with CodeBERT and return copies.

    For every bug with a valid line number, runs the bug line plus its
    configured context window through the classifier, attaches
    ``confidence`` = P(buggy), and sets ``flagged`` to True when confidence
    is below the configured threshold. Inference runs on a worker thread
    so it doesn't block the FastAPI event loop.

    Bugs are passed through untouched when:
    - the model failed to load (``_model`` is None),
    - ``line_number`` is None or out of range,
    - inference raises an exception.
    """
    if not predicted_bugs or _model is None or _tokenizer is None:
        return predicted_bugs

    settings = get_settings()
    window = max(0, settings.codebert_context_window)
    validated: list[PredictedBug] = []
    for bug in predicted_bugs:
        snippet = _extract_snippet(code, bug.line_number, window=window)
        if not snippet:
            validated.append(bug)
            continue
        try:
            p_buggy = await asyncio.to_thread(_score_snippet, snippet)
            validated.append(
                bug.model_copy(
                    update={
                        "confidence": p_buggy,
                        "flagged": p_buggy < settings.codebert_flag_threshold,
                    }
                )
            )
        except Exception as exc:
            logger.warning(
                "CodeBERT inference failed for line %s: %s", bug.line_number, exc
            )
            validated.append(bug)
    return validated
