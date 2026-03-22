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


# ---------------------------------------------------------------------------
# Naming convention checks
# ---------------------------------------------------------------------------


def test_camel_case_function_detected() -> None:
    """A camelCase function name produces a naming_convention finding."""
    code = 'def myFunction():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    naming = [f for f in findings if f.issue_type == "naming_convention"]
    assert any("myFunction" in f.message for f in naming)


def test_snake_case_function_not_flagged() -> None:
    """A snake_case function name produces no naming_convention finding."""
    code = 'def my_function():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    naming = [f for f in findings if f.issue_type == "naming_convention"]
    assert not any("my_function" in f.message for f in naming)


def test_non_pascal_case_class_detected() -> None:
    """A non-PascalCase class name produces a naming_convention finding."""
    code = 'class my_class:\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    naming = [f for f in findings if f.issue_type == "naming_convention"]
    assert any("my_class" in f.message for f in naming)


def test_pascal_case_class_not_flagged() -> None:
    """A PascalCase class name produces no naming_convention finding."""
    code = 'class MyClass:\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    naming = [f for f in findings if f.issue_type == "naming_convention"]
    assert not any("MyClass" in f.message for f in naming)


def test_ambiguous_name_detected() -> None:
    """Single-char names l, O, I produce ambiguous_name findings."""
    code = 'def foo():\n    """Doc."""\n    l = 1\n    O = 2\n    I = 3\n'
    findings, _ = run_static_analysis(code)
    ambig = [f for f in findings if f.issue_type == "ambiguous_name"]
    assert len(ambig) == 3


def test_ambiguous_name_not_flagged_for_other_singles() -> None:
    """Single-char names like x, y, i are not ambiguous."""
    code = 'def foo():\n    """Doc."""\n    x = 1\n    i = 2\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "ambiguous_name" for f in findings)


def test_camel_case_variable_detected() -> None:
    """A camelCase variable assignment produces a naming_convention finding."""
    code = 'def foo():\n    """Doc."""\n    myVar = 1\n'
    findings, _ = run_static_analysis(code)
    naming = [f for f in findings if f.issue_type == "naming_convention"]
    assert any("myVar" in f.message for f in naming)


# ---------------------------------------------------------------------------
# self/cls checks
# ---------------------------------------------------------------------------


def test_wrong_self_detected() -> None:
    """Instance method not using 'self' is flagged."""
    code = (
        "class Foo:\n"
        '    """Doc."""\n'
        "    def method(this):\n"
        '        """Doc."""\n'
        "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    sc = [f for f in findings if f.issue_type == "self_cls_naming"]
    assert len(sc) == 1
    assert "self" in sc[0].message


def test_correct_self_not_flagged() -> None:
    """Instance method using 'self' is not flagged."""
    code = (
        "class Foo:\n"
        '    """Doc."""\n'
        "    def method(self):\n"
        '        """Doc."""\n'
        "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "self_cls_naming" for f in findings)


def test_wrong_cls_detected() -> None:
    """Classmethod not using 'cls' is flagged."""
    code = (
        "class Foo:\n"
        '    """Doc."""\n'
        "    @classmethod\n"
        "    def create(self):\n"
        '        """Doc."""\n'
        "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    sc = [f for f in findings if f.issue_type == "self_cls_naming"]
    assert len(sc) == 1
    assert "cls" in sc[0].message


def test_staticmethod_not_flagged() -> None:
    """Static methods are exempt from self/cls checks."""
    code = (
        "class Foo:\n"
        '    """Doc."""\n'
        "    @staticmethod\n"
        "    def helper(x):\n"
        '        """Doc."""\n'
        "        return x\n"
    )
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "self_cls_naming" for f in findings)


# ---------------------------------------------------------------------------
# None comparison
# ---------------------------------------------------------------------------


def test_none_equality_detected() -> None:
    """``== None`` produces a none_comparison finding."""
    code = 'def foo():\n    """Doc."""\n    if x == None:\n        pass\n'
    findings, _ = run_static_analysis(code)
    nc = [f for f in findings if f.issue_type == "none_comparison"]
    assert len(nc) == 1
    assert nc[0].severity == "Med"


def test_none_is_not_flagged() -> None:
    """``is None`` does not produce a none_comparison finding."""
    code = 'def foo():\n    """Doc."""\n    if x is None:\n        pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "none_comparison" for f in findings)


# ---------------------------------------------------------------------------
# Boolean comparison
# ---------------------------------------------------------------------------


def test_boolean_comparison_detected() -> None:
    """``== True`` produces a boolean_comparison finding."""
    code = 'def foo():\n    """Doc."""\n    if x == True:\n        pass\n'
    findings, _ = run_static_analysis(code)
    bc = [f for f in findings if f.issue_type == "boolean_comparison"]
    assert len(bc) == 1


def test_boolean_comparison_not_flagged_for_direct_use() -> None:
    """Using a boolean directly does not produce a boolean_comparison."""
    code = 'def foo():\n    """Doc."""\n    if x:\n        pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "boolean_comparison" for f in findings)


# ---------------------------------------------------------------------------
# Type comparison
# ---------------------------------------------------------------------------


def test_type_comparison_detected() -> None:
    """``type(x) is type(y)`` produces a type_comparison finding."""
    code = (
        "def foo():\n"
        '    """Doc."""\n'
        "    if type(x) is type(y):\n"
        "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    tc = [f for f in findings if f.issue_type == "type_comparison"]
    assert len(tc) == 1
    assert tc[0].severity == "Med"


def test_isinstance_not_flagged() -> None:
    """``isinstance()`` does not produce a type_comparison finding."""
    code = (
        "def foo():\n"
        '    """Doc."""\n'
        "    if isinstance(x, int):\n"
        "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "type_comparison" for f in findings)


# ---------------------------------------------------------------------------
# Empty sequence check
# ---------------------------------------------------------------------------


def test_len_equals_zero_detected() -> None:
    """``len(x) == 0`` produces an empty_sequence_check finding."""
    code = (
        "def foo():\n" '    """Doc."""\n' "    if len(items) == 0:\n" "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    es = [f for f in findings if f.issue_type == "empty_sequence_check"]
    assert len(es) == 1


def test_truthiness_not_flagged() -> None:
    """``if not items:`` does not produce an empty_sequence_check."""
    code = "def foo():\n" '    """Doc."""\n' "    if not items:\n" "        pass\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "empty_sequence_check" for f in findings)


# ---------------------------------------------------------------------------
# Lambda assignment
# ---------------------------------------------------------------------------


def test_lambda_assignment_detected() -> None:
    """``f = lambda x: x`` produces a lambda_assignment finding."""
    code = "f = lambda x: x\n"
    findings, _ = run_static_analysis(code)
    la = [f for f in findings if f.issue_type == "lambda_assignment"]
    assert len(la) == 1


def test_lambda_in_call_not_flagged() -> None:
    """A lambda passed as an argument is not flagged."""
    code = 'def foo():\n    """Doc."""\n    sorted(items, key=lambda x: x)\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "lambda_assignment" for f in findings)


# ---------------------------------------------------------------------------
# Import formatting
# ---------------------------------------------------------------------------


def test_multi_import_detected() -> None:
    """``import os, sys`` produces an import_formatting finding."""
    code = 'import os, sys\ndef foo():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    imp = [f for f in findings if f.issue_type == "import_formatting"]
    assert len(imp) == 1


def test_separate_imports_not_flagged() -> None:
    """Separate import statements are not flagged."""
    code = "import os\nimport sys\n" 'def foo():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "import_formatting" for f in findings)


def test_from_import_multi_names_not_flagged() -> None:
    """``from os.path import join, exists`` is acceptable."""
    code = "from os.path import join, exists\n" 'def foo():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "import_formatting" for f in findings)


# ---------------------------------------------------------------------------
# is not preference
# ---------------------------------------------------------------------------


def test_not_is_detected() -> None:
    """``not x is y`` produces an is_not_preference finding."""
    code = "def foo():\n" '    """Doc."""\n' "    if not x is None:\n" "        pass\n"
    findings, _ = run_static_analysis(code)
    inp = [f for f in findings if f.issue_type == "is_not_preference"]
    assert len(inp) == 1


def test_is_not_not_flagged() -> None:
    """``x is not None`` does not produce an is_not_preference finding."""
    code = "def foo():\n" '    """Doc."""\n' "    if x is not None:\n" "        pass\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "is_not_preference" for f in findings)


# ---------------------------------------------------------------------------
# Return consistency
# ---------------------------------------------------------------------------


def test_inconsistent_returns_detected() -> None:
    """Mixed return-with-value and bare return produces a finding."""
    code = (
        "def foo(x):\n"
        '    """Doc."""\n'
        "    if x:\n"
        "        return 1\n"
        "    return\n"
    )
    findings, _ = run_static_analysis(code)
    rc = [f for f in findings if f.issue_type == "return_consistency"]
    assert len(rc) == 1
    assert rc[0].severity == "Med"


def test_consistent_returns_not_flagged() -> None:
    """All returns with values does not produce a finding."""
    code = (
        "def foo(x):\n"
        '    """Doc."""\n'
        "    if x:\n"
        "        return 1\n"
        "    return 0\n"
    )
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "return_consistency" for f in findings)


# ---------------------------------------------------------------------------
# Exception inheritance
# ---------------------------------------------------------------------------


def test_base_exception_inheritance_detected() -> None:
    """Inheriting from BaseException is flagged."""
    code = "class MyError(BaseException):\n" '    """Doc."""\n' "    pass\n"
    findings, _ = run_static_analysis(code)
    ei = [f for f in findings if f.issue_type == "exception_inheritance"]
    assert len(ei) == 1
    assert "MyError" in ei[0].message


def test_exception_inheritance_not_flagged() -> None:
    """Inheriting from Exception is not flagged."""
    code = "class MyError(Exception):\n" '    """Doc."""\n' "    pass\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "exception_inheritance" for f in findings)


# ---------------------------------------------------------------------------
# String slicing
# ---------------------------------------------------------------------------


def test_string_prefix_slicing_detected() -> None:
    """``s[:3] == 'foo'`` produces a string_slicing finding."""
    code = (
        "def foo():\n" '    """Doc."""\n' '    if name[:3] == "foo":\n' "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    ss = [f for f in findings if f.issue_type == "string_slicing"]
    assert len(ss) == 1
    assert "startswith" in ss[0].message


def test_string_suffix_slicing_detected() -> None:
    """``s[-3:] == 'bar'`` produces a string_slicing finding."""
    code = (
        "def foo():\n"
        '    """Doc."""\n'
        '    if name[-3:] == "bar":\n'
        "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    ss = [f for f in findings if f.issue_type == "string_slicing"]
    assert len(ss) == 1
    assert "endswith" in ss[0].message


def test_startswith_not_flagged() -> None:
    """Using ``.startswith()`` does not produce a string_slicing finding."""
    code = (
        "def foo():\n"
        '    """Doc."""\n'
        '    if name.startswith("foo"):\n'
        "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "string_slicing" for f in findings)
