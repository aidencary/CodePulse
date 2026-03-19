"""Unit tests for the static analysis engine."""

from app.models.analysis import Finding, PredictedBug
from app.services.analysis_engine import compute_score, run_static_analysis


# Long-line detection
def test_long_line_detected() -> None:
    """A line with 89 characters produces one Low finding."""
    code = "x = " + "a" * 85  # 4 + 85 = 89 chars
    findings, _ = run_static_analysis(code)
    long_line_findings = [f for f in findings if f.issue_type == "long_line"]
    assert len(long_line_findings) == 1
    assert long_line_findings[0].severity == "Low"
    assert long_line_findings[0].line_number == 1


def test_long_line_not_flagged_at_exactly_88() -> None:
    """A line of exactly 88 characters produces no long_line finding."""
    code = "x = " + "a" * 84  # 4 + 84 = 88 chars
    findings, _ = run_static_analysis(code)
    long_line_findings = [f for f in findings if f.issue_type == "long_line"]
    assert len(long_line_findings) == 0


def test_long_line_not_flagged_below_limit() -> None:
    """A short one-liner produces no long_line finding."""
    findings, _ = run_static_analysis("x = 1\n")
    assert not any(f.issue_type == "long_line" for f in findings)


# Missing-docstring detection
def test_missing_docstring_on_function() -> None:
    """A function without a docstring produces one Low finding."""
    code = "def foo():\n    pass\n"
    findings, _ = run_static_analysis(code)
    ds_findings = [f for f in findings if f.issue_type == "missing_docstring"]
    assert len(ds_findings) == 1
    assert ds_findings[0].severity == "Low"
    assert ds_findings[0].line_number == 1


def test_missing_docstring_not_flagged_when_present() -> None:
    """A function with a docstring produces no missing_docstring finding."""
    code = 'def foo():\n    """Does something."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "missing_docstring" for f in findings)


def test_dunder_method_not_flagged_for_missing_docstring() -> None:
    """Dunder methods are exempt from the docstring requirement."""
    code = "class Foo:\n    def __init__(self):\n        pass\n"
    findings, _ = run_static_analysis(code)
    # __init__ should be skipped; the class itself should be flagged
    flagged_names = [f.message for f in findings if f.issue_type == "missing_docstring"]
    assert not any("__init__" in m for m in flagged_names)


def test_missing_docstring_on_class() -> None:
    """A class without a docstring produces a missing_docstring finding."""
    code = "class Bar:\n    pass\n"
    findings, _ = run_static_analysis(code)
    ds_findings = [f for f in findings if f.issue_type == "missing_docstring"]
    assert len(ds_findings) == 1
    assert "Bar" in ds_findings[0].message


# Bare-except detection
def test_bare_except_detected() -> None:
    """A bare ``except:`` clause produces one Med finding."""
    code = "try:\n    pass\nexcept:\n    pass\n"
    findings, _ = run_static_analysis(code)
    bare_findings = [f for f in findings if f.issue_type == "bare_except"]
    assert len(bare_findings) == 1
    assert bare_findings[0].severity == "Med"
    assert bare_findings[0].line_number == 3


def test_bare_except_not_flagged_with_type() -> None:
    """``except Exception:`` is not a bare except."""
    code = "try:\n    pass\nexcept Exception:\n    pass\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "bare_except" for f in findings)


# Syntax-error handling
def test_syntax_error_returns_high_finding() -> None:
    """Invalid syntax produces exactly one High finding and no other checks run."""
    code = "def foo(:\n    pass\n"
    findings, _ = run_static_analysis(code)
    assert len(findings) == 1
    assert findings[0].issue_type == "syntax_error"
    assert findings[0].severity == "High"


# Score computation
def test_score_is_100_for_clean_code() -> None:
    """Clean code with no findings returns a score of 100."""
    code = 'def foo():\n    """Return 1."""\n    return 1\n'
    _, raw_score = run_static_analysis(code)
    # No predicted_bugs, so compute_score == raw_score
    assert raw_score == 100


def test_score_decreases_with_findings() -> None:
    """Multiple findings reduce the score below 100."""
    code = "def foo():\n    pass\n"  # missing docstring (Low = -2)
    findings, raw_score = run_static_analysis(code)
    assert raw_score < 100
    assert raw_score == 98  # 100 - 2 (Low)


def test_score_floor_is_zero() -> None:
    """Many severe findings do not produce a negative score."""
    high_findings = [
        Finding(issue_type="syntax_error", line_number=1, severity="High", message="x")
        for _ in range(20)
    ]
    score = compute_score(high_findings, [])
    assert score == 0


def test_compute_score_includes_predicted_bugs() -> None:
    """Predicted bugs reduce the score beyond the static-findings baseline."""
    findings = [
        Finding(issue_type="long_line", line_number=1, severity="Low", message="x")
    ]
    bugs = [
        PredictedBug(
            line_number=None,
            bug_type="null_deref",
            severity="critical",
            description="x",
            suggested_fix="y",
        )
    ]
    score = compute_score(findings, bugs)
    # 100 - 2 (Low) - 8 (critical) = 90
    assert score == 90
