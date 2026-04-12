"""Unit tests for the CodeBERT validation layer.

Model and tokenizer are replaced with lightweight fakes that return
deterministic logits, so no real model download or torch computation
happens (beyond a tiny softmax on a 2-element tensor).
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from app.models.analysis import PredictedBug
from app.services import codebert_validator


def _make_bug(line_number: int | None = 1) -> PredictedBug:
    return PredictedBug(
        line_number=line_number,
        bug_type="null_dereference",
        severity="medium",
        description="Possible null dereference.",
        suggested_fix="Add a None check.",
    )


class _FakeTokenizer:
    """Tokenizer stub — records calls but returns an empty dict.

    The fake model ignores its kwargs, so the dict contents don't matter.
    """

    def __init__(self) -> None:
        self.calls: list[str] = []

    def __call__(self, text, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(text)
        return {}


class _FakeModel:
    """Stub returning a fixed ``P(buggy)`` via a softmax-invertible logit pair."""

    def __init__(self, p_buggy: float) -> None:
        # Label 0 = buggy for this checkpoint, so build logits
        # [log(p), log(1 - p)] to produce softmax [p_buggy, p_clean].
        import torch

        self._logits = torch.tensor([[math.log(p_buggy), math.log(1 - p_buggy)]])

    def __call__(self, **kwargs):  # type: ignore[no-untyped-def]
        return SimpleNamespace(logits=self._logits)

    def eval(self) -> None:
        pass


def _install_fakes(
    monkeypatch: pytest.MonkeyPatch, p_buggy: float
) -> tuple[_FakeModel, _FakeTokenizer]:
    model = _FakeModel(p_buggy)
    tokenizer = _FakeTokenizer()
    monkeypatch.setattr(codebert_validator, "_model", model)
    monkeypatch.setattr(codebert_validator, "_tokenizer", tokenizer)
    return model, tokenizer


# ---------------------------------------------------------------------------
# Line-extraction helper
# ---------------------------------------------------------------------------


def test_extract_snippet_single_line() -> None:
    code = "a = 1\n  b = 2\nc = 3\n"
    assert codebert_validator._extract_snippet(code, 2, window=0) == "b = 2"


def test_extract_snippet_with_context_dedents() -> None:
    code = "def f():\n    x = None\n    x.foo()\n    return x\n"
    # ±1 around line 3 → lines 2..4; common indent (4 spaces) stripped.
    assert (
        codebert_validator._extract_snippet(code, 3, window=1)
        == "x = None\nx.foo()\nreturn x"
    )


def test_extract_snippet_clamps_to_file_bounds() -> None:
    code = "a = 1\nb = 2\nc = 3\n"
    # window extends past start/end — should just return whatever's in range.
    assert codebert_validator._extract_snippet(code, 1, window=5) == (
        "a = 1\nb = 2\nc = 3"
    )


def test_extract_snippet_handles_none() -> None:
    assert codebert_validator._extract_snippet("x = 1\n", None, window=2) == ""


def test_extract_snippet_handles_out_of_range() -> None:
    assert codebert_validator._extract_snippet("x = 1\n", 9999, window=2) == ""


def test_extract_snippet_strips_inline_comments() -> None:
    # Inline hint comments leak the label and must not reach the model.
    code = "user = None\nprint(user.name)  # null deref here\n"
    assert (
        codebert_validator._extract_snippet(code, 2, window=1)
        == "user = None\nprint(user.name)"
    )


def test_resolve_buggy_index_reads_label2id() -> None:
    class _Cfg:
        label2id = {"clean": 0, "buggy": 1}

    class _M:
        config = _Cfg()

    assert codebert_validator._resolve_buggy_index(_M()) == 1


def test_resolve_buggy_index_case_insensitive() -> None:
    class _Cfg:
        label2id = {"CLEAN": 0, "Buggy": 1}

    class _M:
        config = _Cfg()

    assert codebert_validator._resolve_buggy_index(_M()) == 1


def test_resolve_buggy_index_falls_back_to_zero_for_placeholders() -> None:
    class _Cfg:
        label2id = {"LABEL_0": 0, "LABEL_1": 1}

    class _M:
        config = _Cfg()

    assert codebert_validator._resolve_buggy_index(_M()) == 0


def test_resolve_buggy_index_handles_missing_config() -> None:
    assert codebert_validator._resolve_buggy_index(object()) == 0


def test_strip_comments_preserves_string_literals() -> None:
    assert (
        codebert_validator._strip_comments('url = "http://x"  # note')
        == 'url = "http://x"  '
    )
    assert (
        codebert_validator._strip_comments("s = '# not a comment'")
        == "s = '# not a comment'"
    )


# ---------------------------------------------------------------------------
# validate_predictions — confidence + flagged logic
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_high_confidence_not_flagged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fakes(monkeypatch, p_buggy=0.8)
    result = await codebert_validator.validate_predictions("x = 1\n", [_make_bug()])
    assert len(result) == 1
    assert result[0].confidence == pytest.approx(0.8, abs=1e-5)
    assert result[0].flagged is False


@pytest.mark.asyncio
async def test_validate_low_confidence_flagged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fakes(monkeypatch, p_buggy=0.05)
    result = await codebert_validator.validate_predictions("x = 1\n", [_make_bug()])
    assert result[0].confidence == pytest.approx(0.05, abs=1e-5)
    assert result[0].flagged is True


@pytest.mark.asyncio
async def test_validate_threshold_boundary_is_not_flagged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Just above the default threshold (0.3), ``flagged`` should stay False —
    # the comparison is strict ``<``.
    _install_fakes(monkeypatch, p_buggy=0.31)
    result = await codebert_validator.validate_predictions("x = 1\n", [_make_bug()])
    assert result[0].flagged is False


@pytest.mark.asyncio
async def test_validate_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fakes(monkeypatch, p_buggy=0.9)
    assert await codebert_validator.validate_predictions("x = 1\n", []) == []


@pytest.mark.asyncio
async def test_validate_line_number_none_passes_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, tokenizer = _install_fakes(monkeypatch, p_buggy=0.9)
    bug = _make_bug(line_number=None)
    result = await codebert_validator.validate_predictions("x = 1\n", [bug])
    assert result == [bug]  # untouched
    assert tokenizer.calls == []  # tokenizer never called


@pytest.mark.asyncio
async def test_validate_line_number_out_of_range_passes_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, tokenizer = _install_fakes(monkeypatch, p_buggy=0.9)
    bug = _make_bug(line_number=9999)
    result = await codebert_validator.validate_predictions("x = 1\n", [bug])
    assert result == [bug]
    assert tokenizer.calls == []


@pytest.mark.asyncio
async def test_validate_no_model_loaded_passes_through() -> None:
    # The autouse conftest fixture already sets _model and _tokenizer to None.
    bug = _make_bug()
    result = await codebert_validator.validate_predictions("x = 1\n", [bug])
    assert result == [bug]


@pytest.mark.asyncio
async def test_validate_inference_failure_passes_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _ExplodingModel:
        def __call__(self, **kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("boom")

        def eval(self) -> None:
            pass

    monkeypatch.setattr(codebert_validator, "_model", _ExplodingModel())
    monkeypatch.setattr(codebert_validator, "_tokenizer", _FakeTokenizer())
    bug = _make_bug()
    result = await codebert_validator.validate_predictions("x = 1\n", [bug])
    # Safe fallback — bug returned untouched, confidence still None.
    assert result[0].confidence is None
    assert result[0].flagged is False
