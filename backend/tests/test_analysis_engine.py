"""Unit tests for the static analysis engine."""

import pytest

from app.models.analysis import Finding, PredictedBug
from app.services.engines.python_engine import PythonEngine

pycodestyle = pytest.importorskip("pycodestyle")

compute_score = PythonEngine.compute_score
run_static_analysis = PythonEngine.run_static_analysis


class _CollectPycodestyleReport(pycodestyle.BaseReport):
    """Collect pycodestyle error codes for snippet parity checks."""

    def __init__(self, options: object) -> None:
        super().__init__(options)
        self.codes: list[str] = []

    def error(
        self,
        line_number: int,
        offset: int,
        text: str,
        check: object,
    ) -> int:
        self.codes.append(text[:4])
        return super().error(line_number, offset, text, check)


def _pycodestyle_codes(code: str) -> set[str]:
    """Return pycodestyle error codes raised for a source snippet."""
    style = pycodestyle.StyleGuide(quiet=True)
    report = _CollectPycodestyleReport(style.options)
    checker = pycodestyle.Checker(
        lines=code.splitlines(True),
        options=style.options,
        report=report,
    )
    checker.check_all()
    return set(report.codes)


# Long-line detection
# TC-ANALYSIS-001
def test_long_line_detected() -> None:
    """A line with 89 characters produces one Low finding."""
    code = "x = " + "a" * 85  # 4 + 85 = 89 chars
    findings, _ = run_static_analysis(code)
    long_line_findings = [f for f in findings if f.issue_type == "long_line"]
    assert len(long_line_findings) == 1
    assert long_line_findings[0].severity == "Low"
    assert long_line_findings[0].line_number == 1


# TC-ANALYSIS-002
def test_long_line_not_flagged_at_exactly_88() -> None:
    """A line of exactly 88 characters produces no long_line finding."""
    code = "x = " + "a" * 84  # 4 + 84 = 88 chars
    findings, _ = run_static_analysis(code)
    long_line_findings = [f for f in findings if f.issue_type == "long_line"]
    assert len(long_line_findings) == 0


# TC-ANALYSIS-003
def test_long_line_not_flagged_below_limit() -> None:
    """A short one-liner produces no long_line finding."""
    findings, _ = run_static_analysis("x = 1\n")
    assert not any(f.issue_type == "long_line" for f in findings)


# Missing-docstring detection
# TC-ANALYSIS-004
def test_missing_docstring_on_function() -> None:
    """A function without a docstring produces one Low finding."""
    code = "def foo():\n    pass\n"
    findings, _ = run_static_analysis(code)
    ds_findings = [f for f in findings if f.issue_type == "missing_docstring"]
    assert len(ds_findings) == 1
    assert ds_findings[0].severity == "Low"
    assert ds_findings[0].line_number == 1


# TC-ANALYSIS-005
def test_missing_docstring_not_flagged_when_present() -> None:
    """A function with a docstring produces no missing_docstring finding."""
    code = 'def foo():\n    """Does something."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "missing_docstring" for f in findings)


# TC-ANALYSIS-006
def test_dunder_method_not_flagged_for_missing_docstring() -> None:
    """Dunder methods are exempt from the docstring requirement."""
    code = "class Foo:\n    def __init__(self):\n        pass\n"
    findings, _ = run_static_analysis(code)
    # __init__ should be skipped; the class itself should be flagged
    flagged_names = [f.message for f in findings if f.issue_type == "missing_docstring"]
    assert not any("__init__" in m for m in flagged_names)


# TC-ANALYSIS-007
def test_missing_docstring_on_class() -> None:
    """A class without a docstring produces a missing_docstring finding."""
    code = "class Bar:\n    pass\n"
    findings, _ = run_static_analysis(code)
    ds_findings = [f for f in findings if f.issue_type == "missing_docstring"]
    assert len(ds_findings) == 1
    assert "Bar" in ds_findings[0].message


# Bare-except detection
# TC-ANALYSIS-008
def test_bare_except_detected() -> None:
    """A bare ``except:`` clause produces one Med finding."""
    code = "try:\n    pass\nexcept:\n    pass\n"
    findings, _ = run_static_analysis(code)
    bare_findings = [f for f in findings if f.issue_type == "bare_except"]
    assert len(bare_findings) == 1
    assert bare_findings[0].severity == "Med"
    assert bare_findings[0].line_number == 3


# TC-ANALYSIS-009
def test_bare_except_not_flagged_with_type() -> None:
    """``except Exception:`` is not a bare except."""
    code = "try:\n    pass\nexcept Exception:\n    pass\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "bare_except" for f in findings)


# Syntax-error handling
# TC-ANALYSIS-010
def test_syntax_error_returns_high_finding() -> None:
    """Invalid syntax produces exactly one High finding and no other checks run."""
    code = "def foo(:\n    pass\n"
    findings, _ = run_static_analysis(code)
    assert len(findings) == 1
    assert findings[0].issue_type == "syntax_error"
    assert findings[0].severity == "High"


# Score computation
# TC-ANALYSIS-011
def test_score_is_100_for_clean_code() -> None:
    """Clean code with no findings returns a score of 100."""
    code = 'def foo():\n    """Return 1."""\n    return 1\n'
    _, raw_score = run_static_analysis(code)
    # No predicted_bugs, so compute_score == raw_score
    assert raw_score == 100


# TC-ANALYSIS-012
def test_score_decreases_with_findings() -> None:
    """Multiple findings reduce the score below 100."""
    code = "def foo():\n    pass\n"  # missing docstring (Low = -2)
    findings, raw_score = run_static_analysis(code)
    assert raw_score < 100
    assert raw_score == 98  # 100 - 2 (Low)


# TC-ANALYSIS-013
def test_score_floor_is_zero() -> None:
    """Many severe findings do not produce a negative score."""
    high_findings = [
        Finding(issue_type="syntax_error", line_number=1, severity="High", message="x")
        for _ in range(20)
    ]
    score = compute_score(high_findings, [])
    assert score == 0


# TC-ANALYSIS-014
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


# TC-ANALYSIS-014b — CodeBERT validation
def test_compute_score_skips_flagged_bugs() -> None:
    """Bugs flagged by CodeBERT as likely false positives incur no penalty."""
    bugs = [
        PredictedBug(
            line_number=1,
            bug_type="null_deref",
            severity="critical",
            description="x",
            suggested_fix="y",
            confidence=0.1,
            flagged=True,
        )
    ]
    assert compute_score([], bugs) == 100


def test_compute_score_penalises_unflagged_bugs_only() -> None:
    """A mix of flagged and unflagged bugs only counts the unflagged ones."""
    bugs = [
        PredictedBug(
            line_number=1,
            bug_type="null_deref",
            severity="critical",
            description="x",
            suggested_fix="y",
            confidence=0.1,
            flagged=True,
        ),
        PredictedBug(
            line_number=2,
            bug_type="off_by_one",
            severity="medium",
            description="x",
            suggested_fix="y",
            confidence=0.9,
            flagged=False,
        ),
    ]
    # Only the medium bug counts: 100 - 2 (medium) = 98.
    assert compute_score([], bugs) == 98


# ---------------------------------------------------------------------------
# Naming convention checks
# ---------------------------------------------------------------------------


# TC-ANALYSIS-015
def test_camel_case_function_detected() -> None:
    """A camelCase function name produces a naming_convention finding."""
    code = 'def myFunction():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    naming = [f for f in findings if f.issue_type == "naming_convention"]
    assert any("myFunction" in f.message for f in naming)


# TC-ANALYSIS-016
def test_snake_case_function_not_flagged() -> None:
    """A snake_case function name produces no naming_convention finding."""
    code = 'def my_function():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    naming = [f for f in findings if f.issue_type == "naming_convention"]
    assert not any("my_function" in f.message for f in naming)


# TC-ANALYSIS-017
def test_non_pascal_case_class_detected() -> None:
    """A non-PascalCase class name produces a naming_convention finding."""
    code = 'class my_class:\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    naming = [f for f in findings if f.issue_type == "naming_convention"]
    assert any("my_class" in f.message for f in naming)


# TC-ANALYSIS-018
def test_pascal_case_class_not_flagged() -> None:
    """A PascalCase class name produces no naming_convention finding."""
    code = 'class MyClass:\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    naming = [f for f in findings if f.issue_type == "naming_convention"]
    assert not any("MyClass" in f.message for f in naming)


# TC-ANALYSIS-019
def test_ambiguous_name_detected() -> None:
    """Single-char names l, O, I produce ambiguous_name findings."""
    code = 'def foo():\n    """Doc."""\n    l = 1\n    O = 2\n    I = 3\n'
    findings, _ = run_static_analysis(code)
    ambig = [f for f in findings if f.issue_type == "ambiguous_name"]
    assert len(ambig) == 3


# TC-ANALYSIS-020
def test_ambiguous_name_not_flagged_for_other_singles() -> None:
    """Single-char names like x, y, i are not ambiguous."""
    code = 'def foo():\n    """Doc."""\n    x = 1\n    i = 2\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "ambiguous_name" for f in findings)


# TC-ANALYSIS-021
def test_camel_case_variable_detected() -> None:
    """A camelCase variable assignment produces a naming_convention finding."""
    code = 'def foo():\n    """Doc."""\n    myVar = 1\n'
    findings, _ = run_static_analysis(code)
    naming = [f for f in findings if f.issue_type == "naming_convention"]
    assert any("myVar" in f.message for f in naming)


# ---------------------------------------------------------------------------
# self/cls checks
# ---------------------------------------------------------------------------


# TC-ANALYSIS-022
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


# TC-ANALYSIS-023
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


# TC-ANALYSIS-024
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


# TC-ANALYSIS-025
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


# TC-ANALYSIS-026
def test_none_equality_detected() -> None:
    """``== None`` produces a none_comparison finding."""
    code = 'def foo():\n    """Doc."""\n    if x == None:\n        pass\n'
    findings, _ = run_static_analysis(code)
    nc = [f for f in findings if f.issue_type == "none_comparison"]
    assert len(nc) == 1
    assert nc[0].severity == "Med"


# TC-ANALYSIS-027
def test_none_is_not_flagged() -> None:
    """``is None`` does not produce a none_comparison finding."""
    code = 'def foo():\n    """Doc."""\n    if x is None:\n        pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "none_comparison" for f in findings)


# ---------------------------------------------------------------------------
# Boolean comparison
# ---------------------------------------------------------------------------


# TC-ANALYSIS-028
def test_boolean_comparison_detected() -> None:
    """``== True`` produces a boolean_comparison finding."""
    code = 'def foo():\n    """Doc."""\n    if x == True:\n        pass\n'
    findings, _ = run_static_analysis(code)
    bc = [f for f in findings if f.issue_type == "boolean_comparison"]
    assert len(bc) == 1


# TC-ANALYSIS-029
def test_boolean_comparison_not_flagged_for_direct_use() -> None:
    """Using a boolean directly does not produce a boolean_comparison."""
    code = 'def foo():\n    """Doc."""\n    if x:\n        pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "boolean_comparison" for f in findings)


# ---------------------------------------------------------------------------
# Type comparison
# ---------------------------------------------------------------------------


# TC-ANALYSIS-030
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


# TC-ANALYSIS-031
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


# TC-ANALYSIS-032
def test_len_equals_zero_detected() -> None:
    """``len(x) == 0`` produces an empty_sequence_check finding."""
    code = (
        "def foo():\n" '    """Doc."""\n' "    if len(items) == 0:\n" "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    es = [f for f in findings if f.issue_type == "empty_sequence_check"]
    assert len(es) == 1


# TC-ANALYSIS-033
def test_truthiness_not_flagged() -> None:
    """``if not items:`` does not produce an empty_sequence_check."""
    code = "def foo():\n" '    """Doc."""\n' "    if not items:\n" "        pass\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "empty_sequence_check" for f in findings)


# ---------------------------------------------------------------------------
# Lambda assignment
# ---------------------------------------------------------------------------


# TC-ANALYSIS-034
def test_lambda_assignment_detected() -> None:
    """``f = lambda x: x`` produces a lambda_assignment finding."""
    code = "f = lambda x: x\n"
    findings, _ = run_static_analysis(code)
    la = [f for f in findings if f.issue_type == "lambda_assignment"]
    assert len(la) == 1


# TC-ANALYSIS-035
def test_lambda_in_call_not_flagged() -> None:
    """A lambda passed as an argument is not flagged."""
    code = 'def foo():\n    """Doc."""\n    sorted(items, key=lambda x: x)\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "lambda_assignment" for f in findings)


# ---------------------------------------------------------------------------
# Import formatting
# ---------------------------------------------------------------------------


# TC-ANALYSIS-036
def test_multi_import_detected() -> None:
    """``import os, sys`` produces an import_formatting finding."""
    code = 'import os, sys\ndef foo():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    imp = [f for f in findings if f.issue_type == "import_formatting"]
    assert len(imp) == 1


# TC-ANALYSIS-037
def test_separate_imports_not_flagged() -> None:
    """Separate import statements are not flagged."""
    code = "import os\nimport sys\n" 'def foo():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "import_formatting" for f in findings)


# TC-ANALYSIS-038
def test_from_import_multi_names_not_flagged() -> None:
    """``from os.path import join, exists`` is acceptable."""
    code = "from os.path import join, exists\n" 'def foo():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "import_formatting" for f in findings)


# ---------------------------------------------------------------------------
# is not preference
# ---------------------------------------------------------------------------


# TC-ANALYSIS-039
def test_not_is_detected() -> None:
    """``not x is y`` produces an is_not_preference finding."""
    code = "def foo():\n" '    """Doc."""\n' "    if not x is None:\n" "        pass\n"
    findings, _ = run_static_analysis(code)
    inp = [f for f in findings if f.issue_type == "is_not_preference"]
    assert len(inp) == 1


# TC-ANALYSIS-040
def test_is_not_not_flagged() -> None:
    """``x is not None`` does not produce an is_not_preference finding."""
    code = "def foo():\n" '    """Doc."""\n' "    if x is not None:\n" "        pass\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "is_not_preference" for f in findings)


# ---------------------------------------------------------------------------
# Return consistency
# ---------------------------------------------------------------------------


# TC-ANALYSIS-041
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


# TC-ANALYSIS-042
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


# TC-ANALYSIS-043
def test_base_exception_inheritance_detected() -> None:
    """Inheriting from BaseException is flagged."""
    code = "class MyError(BaseException):\n" '    """Doc."""\n' "    pass\n"
    findings, _ = run_static_analysis(code)
    ei = [f for f in findings if f.issue_type == "exception_inheritance"]
    assert len(ei) == 1
    assert "MyError" in ei[0].message


# TC-ANALYSIS-044
def test_exception_inheritance_not_flagged() -> None:
    """Inheriting from Exception is not flagged."""
    code = "class MyError(Exception):\n" '    """Doc."""\n' "    pass\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "exception_inheritance" for f in findings)


# ---------------------------------------------------------------------------
# String slicing
# ---------------------------------------------------------------------------


# TC-ANALYSIS-045
def test_string_prefix_slicing_detected() -> None:
    """``s[:3] == 'foo'`` produces a string_slicing finding."""
    code = (
        "def foo():\n" '    """Doc."""\n' '    if name[:3] == "foo":\n' "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    ss = [f for f in findings if f.issue_type == "string_slicing"]
    assert len(ss) == 1
    assert "startswith" in ss[0].message


# TC-ANALYSIS-046
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


# TC-ANALYSIS-047
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


# ---------------------------------------------------------------------------
# Trailing whitespace
# ---------------------------------------------------------------------------


# TC-ANALYSIS-048
def test_trailing_whitespace_detected() -> None:
    """A line with trailing spaces produces a trailing_whitespace finding."""
    code = "x = 1   \ny = 2\n"
    findings, _ = run_static_analysis(code)
    tw = [f for f in findings if f.issue_type == "trailing_whitespace"]
    assert len(tw) == 1
    assert tw[0].line_number == 1


# TC-ANALYSIS-049
def test_no_trailing_whitespace_not_flagged() -> None:
    """Clean lines produce no trailing_whitespace findings."""
    code = 'def foo():\n    """Doc."""\n    return 1\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "trailing_whitespace" for f in findings)


# ---------------------------------------------------------------------------
# Tab indentation
# ---------------------------------------------------------------------------


# TC-ANALYSIS-050
def test_tab_indentation_detected() -> None:
    """A line indented with a tab produces a tab_indentation finding."""
    code = 'def foo():\n\t"""Doc."""\n\tpass\n'
    findings, _ = run_static_analysis(code)
    ti = [f for f in findings if f.issue_type == "tab_indentation"]
    assert len(ti) == 2
    assert ti[0].severity == "Med"


# TC-ANALYSIS-051
def test_space_indentation_not_flagged() -> None:
    """Lines indented with spaces produce no tab_indentation findings."""
    code = 'def foo():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "tab_indentation" for f in findings)


# ---------------------------------------------------------------------------
# Blank line spacing
# ---------------------------------------------------------------------------


# TC-ANALYSIS-052
def test_missing_blank_lines_before_top_level_def() -> None:
    """A top-level def with < 2 blank lines before it is flagged."""
    code = 'import os\n\ndef foo():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    bl = [f for f in findings if f.issue_type == "blank_line_spacing"]
    assert len(bl) == 1
    assert "2 blank lines" in bl[0].message


# TC-ANALYSIS-053
def test_correct_blank_lines_before_top_level_def() -> None:
    """A top-level def with 2 blank lines before it is not flagged."""
    code = "import os\n\n\n" 'def foo():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "blank_line_spacing" for f in findings)


# TC-ANALYSIS-054
def test_missing_blank_line_between_methods() -> None:
    """Methods without a blank line between them are flagged."""
    code = (
        "class Foo:\n"
        '    """Doc."""\n'
        "    def a(self):\n"
        '        """Doc."""\n'
        "        pass\n"
        "    def b(self):\n"
        '        """Doc."""\n'
        "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    bl = [f for f in findings if f.issue_type == "blank_line_spacing"]
    assert len(bl) == 1
    assert "1 blank line" in bl[0].message


# TC-ANALYSIS-055
def test_correct_blank_line_between_methods() -> None:
    """Methods with 1 blank line between them are not flagged."""
    code = (
        "class Foo:\n"
        '    """Doc."""\n'
        "    def a(self):\n"
        '        """Doc."""\n'
        "        pass\n"
        "\n"
        "    def b(self):\n"
        '        """Doc."""\n'
        "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "blank_line_spacing" for f in findings)


# ---------------------------------------------------------------------------
# Inline comment spacing
# ---------------------------------------------------------------------------


# TC-ANALYSIS-056
def test_inline_comment_too_close_detected() -> None:
    """An inline comment with < 2 spaces before it is flagged."""
    code = 'def foo():\n    """Doc."""\n    x = 1 # bad\n'
    findings, _ = run_static_analysis(code)
    ic = [f for f in findings if f.issue_type == "inline_comment_spacing"]
    assert len(ic) == 1


# TC-ANALYSIS-057
def test_inline_comment_proper_spacing_not_flagged() -> None:
    """An inline comment with 2+ spaces before it is not flagged."""
    code = 'def foo():\n    """Doc."""\n    x = 1  # good\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "inline_comment_spacing" for f in findings)


# TC-ANALYSIS-058
def test_block_comment_not_flagged_as_inline() -> None:
    """A block comment is not flagged by the inline comment check."""
    code = '# this is a block comment\ndef foo():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "inline_comment_spacing" for f in findings)


# ---------------------------------------------------------------------------
# Comment hash spacing
# ---------------------------------------------------------------------------


# TC-ANALYSIS-059
def test_comment_missing_space_after_hash() -> None:
    """A comment without a space after # is flagged."""
    code = "#bad comment\n"
    findings, _ = run_static_analysis(code)
    cs = [f for f in findings if f.issue_type == "comment_spacing"]
    assert len(cs) == 1


# TC-ANALYSIS-060
def test_comment_with_space_after_hash_not_flagged() -> None:
    """A comment with a space after # is not flagged."""
    code = '# good comment\ndef foo():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "comment_spacing" for f in findings)


# TC-ANALYSIS-061
def test_shebang_not_flagged() -> None:
    """A shebang line is not flagged for missing space after #."""
    code = '#!/usr/bin/env python\ndef foo():\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "comment_spacing" for f in findings)


# ---------------------------------------------------------------------------
# Triple quote style
# ---------------------------------------------------------------------------


# TC-ANALYSIS-062
def test_triple_single_quotes_detected() -> None:
    """Triple single quotes produce a triple_quote_style finding."""
    code = "def foo():\n    '''Bad docstring.'''\n    pass\n"
    findings, _ = run_static_analysis(code)
    tq = [f for f in findings if f.issue_type == "triple_quote_style"]
    assert len(tq) >= 1


# TC-ANALYSIS-063
def test_triple_double_quotes_not_flagged() -> None:
    """Triple double quotes do not produce a triple_quote_style finding."""
    code = 'def foo():\n    """Good docstring."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "triple_quote_style" for f in findings)


# ---------------------------------------------------------------------------
# Import ordering
# ---------------------------------------------------------------------------


# TC-ANALYSIS-064
def test_stdlib_after_third_party_detected() -> None:
    """A stdlib import after a third-party import is flagged."""
    code = (
        "import requests\n"
        "import os\n"
        "\n\n"
        'def foo():\n    """Doc."""\n    pass\n'
    )
    findings, _ = run_static_analysis(code)
    io = [f for f in findings if f.issue_type == "import_ordering"]
    assert len(io) == 1
    assert "os" in io[0].message
    assert "stdlib" in io[0].message


# TC-ANALYSIS-065
def test_properly_grouped_imports_not_flagged() -> None:
    """Imports in correct order (stdlib then third-party) are not flagged."""
    code = (
        "import os\n"
        "import sys\n"
        "\n"
        "import requests\n"
        "\n\n"
        'def foo():\n    """Doc."""\n    pass\n'
    )
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "import_ordering" for f in findings)


# TC-ANALYSIS-065A
def test_local_absolute_before_third_party_detected() -> None:
    """A third-party import after absolute local import is flagged."""
    code = (
        "import app.config\n"
        "import requests\n"
        "\n\n"
        'def foo():\n    """Doc."""\n    pass\n'
    )
    findings, _ = run_static_analysis(code)
    io = [f for f in findings if f.issue_type == "import_ordering"]
    assert len(io) == 1
    assert "third-party" in io[0].message
    assert "local" in io[0].message


# TC-ANALYSIS-065B
def test_proper_grouping_with_local_absolute_not_flagged() -> None:
    """Stdlib, third-party, then absolute local imports are accepted."""
    code = (
        "import os\n"
        "\n"
        "import requests\n"
        "\n"
        "import app.config\n"
        "\n\n"
        'def foo():\n    """Doc."""\n    pass\n'
    )
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "import_ordering" for f in findings)


# ---------------------------------------------------------------------------
# Try block scope
# ---------------------------------------------------------------------------


# TC-ANALYSIS-066
def test_broad_try_block_detected() -> None:
    """A try block with >5 statements is flagged."""
    code = (
        "def foo():\n"
        '    """Doc."""\n'
        "    try:\n"
        "        a = 1\n"
        "        b = 2\n"
        "        c = 3\n"
        "        d = 4\n"
        "        e = 5\n"
        "        f = 6\n"
        "    except Exception:\n"
        "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    ts = [f for f in findings if f.issue_type == "try_block_scope"]
    assert len(ts) == 1
    assert "6 statements" in ts[0].message


# TC-ANALYSIS-067
def test_narrow_try_block_not_flagged() -> None:
    """A try block with <=5 statements is not flagged."""
    code = (
        "def foo():\n"
        '    """Doc."""\n'
        "    try:\n"
        "        a = 1\n"
        "        b = 2\n"
        "    except Exception:\n"
        "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "try_block_scope" for f in findings)


# ---------------------------------------------------------------------------
# Context manager usage
# ---------------------------------------------------------------------------


# TC-ANALYSIS-068
def test_try_finally_close_detected() -> None:
    """A try/finally with .close() is flagged."""
    code = (
        "def foo():\n"
        '    """Doc."""\n'
        "    f = open('test.txt')\n"
        "    try:\n"
        "        data = f.read()\n"
        "    finally:\n"
        "        f.close()\n"
    )
    findings, _ = run_static_analysis(code)
    cm = [f for f in findings if f.issue_type == "context_manager_usage"]
    assert len(cm) == 1
    assert "with" in cm[0].message


# TC-ANALYSIS-069
def test_with_statement_not_flagged() -> None:
    """Using a with statement does not produce a context_manager_usage finding."""
    code = (
        "def foo():\n"
        '    """Doc."""\n'
        "    with open('test.txt') as f:\n"
        "        data = f.read()\n"
    )
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "context_manager_usage" for f in findings)


# ===========================================================================
# New PEP 8 checks (22 checks, 44 tests)
# ===========================================================================


# ---------------------------------------------------------------------------
# is_true_false
# ---------------------------------------------------------------------------


# TC-ANALYSIS-084
def test_is_true_detected() -> None:
    """``is True`` produces an is_true_false finding."""
    code = 'def foo():\n    """Doc."""\n    if x is True:\n        pass\n'
    findings, _ = run_static_analysis(code)
    itf = [f for f in findings if f.issue_type == "is_true_false"]
    assert len(itf) == 1
    assert "truthiness" in itf[0].message.lower()


# TC-ANALYSIS-085
def test_is_true_false_not_flagged_for_direct_use() -> None:
    """Using a boolean value directly does not produce is_true_false."""
    code = 'def foo():\n    """Doc."""\n    if x:\n        pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "is_true_false" for f in findings)


# ---------------------------------------------------------------------------
# exception_naming
# ---------------------------------------------------------------------------


# TC-ANALYSIS-086
def test_exception_naming_missing_error_suffix() -> None:
    """An exception class not ending with 'Error' is flagged."""
    code = 'class MyException(Exception):\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    en = [f for f in findings if f.issue_type == "exception_naming"]
    assert len(en) == 1
    assert "Error" in en[0].message


# TC-ANALYSIS-087
def test_exception_naming_with_error_suffix_not_flagged() -> None:
    """An exception class ending with 'Error' is not flagged."""
    code = 'class MyError(Exception):\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "exception_naming" for f in findings)


# ---------------------------------------------------------------------------
# invalid_dunder
# ---------------------------------------------------------------------------


# TC-ANALYSIS-088
def test_invalid_dunder_detected() -> None:
    """A non-standard dunder method is flagged."""
    code = (
        "class Foo:\n"
        '    """Doc."""\n'
        "    def __custom__(self):\n"
        '        """Doc."""\n'
        "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    idd = [f for f in findings if f.issue_type == "invalid_dunder"]
    assert len(idd) == 1
    assert "__custom__" in idd[0].message


# TC-ANALYSIS-089
def test_valid_dunder_not_flagged() -> None:
    """A standard dunder method is not flagged."""
    code = (
        "class Foo:\n" '    """Doc."""\n' "    def __init__(self):\n" "        pass\n"
    )
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "invalid_dunder" for f in findings)


# ---------------------------------------------------------------------------
# return_in_finally
# ---------------------------------------------------------------------------


# TC-ANALYSIS-090
def test_return_in_finally_detected() -> None:
    """A return inside a finally block is flagged as High severity."""
    code = (
        "def foo():\n"
        '    """Doc."""\n'
        "    try:\n"
        "        pass\n"
        "    finally:\n"
        "        return 1\n"
    )
    findings, _ = run_static_analysis(code)
    rif = [f for f in findings if f.issue_type == "return_in_finally"]
    assert len(rif) == 1
    assert rif[0].severity == "High"


# TC-ANALYSIS-091
def test_no_return_in_finally_not_flagged() -> None:
    """A try/finally without return in finally is not flagged."""
    code = (
        "def foo():\n"
        '    """Doc."""\n'
        "    try:\n"
        "        pass\n"
        "    finally:\n"
        "        x = 1\n"
    )
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "return_in_finally" for f in findings)


# ---------------------------------------------------------------------------
# implicit_return_none
# ---------------------------------------------------------------------------


# TC-ANALYSIS-092
def test_implicit_return_none_detected() -> None:
    """A bare return in a function with return values is flagged."""
    code = (
        "def foo(x):\n"
        '    """Doc."""\n'
        "    if x:\n"
        "        return 1\n"
        "    return\n"
    )
    findings, _ = run_static_analysis(code)
    irn = [f for f in findings if f.issue_type == "implicit_return_none"]
    assert len(irn) == 1
    assert "return None" in irn[0].message


# TC-ANALYSIS-093
def test_implicit_return_none_not_flagged_for_consistent() -> None:
    """A function with only bare returns is not flagged."""
    code = (
        "def foo(x):\n"
        '    """Doc."""\n'
        "    if x:\n"
        "        return\n"
        "    return\n"
    )
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "implicit_return_none" for f in findings)


# ---------------------------------------------------------------------------
# module_dunder_placement
# ---------------------------------------------------------------------------


# TC-ANALYSIS-094
def test_module_dunder_after_import_detected() -> None:
    """__all__ after an import is flagged."""
    code = 'import os\n__all__ = ["foo"]\n'
    findings, _ = run_static_analysis(code)
    mdp = [f for f in findings if f.issue_type == "module_dunder_placement"]
    assert len(mdp) == 1


# TC-ANALYSIS-095
def test_module_dunder_before_import_not_flagged() -> None:
    """__all__ before imports is not flagged."""
    code = '__all__ = ["foo"]\nimport os\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "module_dunder_placement" for f in findings)


# ---------------------------------------------------------------------------
# relative_import
# ---------------------------------------------------------------------------


# TC-ANALYSIS-096
def test_relative_import_detected() -> None:
    """A relative import is flagged."""
    code = "from . import foo\n"
    findings, _ = run_static_analysis(code)
    ri = [f for f in findings if f.issue_type == "relative_import"]
    assert len(ri) == 1


# TC-ANALYSIS-097
def test_absolute_import_not_flagged() -> None:
    """An absolute import is not flagged."""
    code = "import os\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "relative_import" for f in findings)


# ---------------------------------------------------------------------------
# semicolon_statement (E702)
# ---------------------------------------------------------------------------


# TC-ANALYSIS-098
def test_semicolon_statement_detected() -> None:
    """Two statements joined by semicolon are flagged."""
    code = "x = 1; y = 2\n"
    findings, _ = run_static_analysis(code)
    ss = [f for f in findings if f.issue_type == "semicolon_statement"]
    assert len(ss) == 1


# TC-ANALYSIS-099
def test_no_semicolon_not_flagged() -> None:
    """Separate statements on their own lines are not flagged."""
    code = "x = 1\ny = 2\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "semicolon_statement" for f in findings)


# ---------------------------------------------------------------------------
# compound_statement (E701)
# ---------------------------------------------------------------------------


# TC-ANALYSIS-100
def test_compound_statement_detected() -> None:
    """An if/body on a single line is flagged."""
    code = "def foo():\n" '    """Doc."""\n' "    if True: pass\n"
    findings, _ = run_static_analysis(code)
    cs = [f for f in findings if f.issue_type == "compound_statement"]
    assert len(cs) == 1


# TC-ANALYSIS-101
def test_compound_statement_not_flagged_for_multiline() -> None:
    """An if with body on the next line is not flagged."""
    code = "def foo():\n" '    """Doc."""\n' "    if True:\n" "        pass\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "compound_statement" for f in findings)


# ---------------------------------------------------------------------------
# bracket_whitespace (E201/E202)
# ---------------------------------------------------------------------------


# TC-ANALYSIS-102
def test_bracket_whitespace_detected() -> None:
    """Space after opening bracket is flagged."""
    code = "x = foo( 1, 2)\n"
    findings, _ = run_static_analysis(code)
    bw = [f for f in findings if f.issue_type == "bracket_whitespace"]
    assert len(bw) >= 1


# TC-ANALYSIS-103
def test_bracket_whitespace_not_flagged_for_clean() -> None:
    """No space inside brackets is not flagged."""
    code = "x = foo(1, 2)\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "bracket_whitespace" for f in findings)


# TC-ANALYSIS-104
def test_bracket_whitespace_not_flagged_for_tab_indented_multiline_call() -> None:
    """Tab-indented multiline calls do not produce bracket_whitespace."""
    code = (
        "return Enemy(\n"
        "\tname=random.choice(names),\n"
        "\thp=20 + safe_level * 3,\n"
        "\tattack=5 + safe_level,\n"
        "\tdefense=2 + safe_level // 2,\n"
        "\tgold=10 + safe_level * 2,\n"
        "\t)\n"
    )
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "bracket_whitespace" for f in findings)


# TC-ANALYSIS-104A
def test_bracket_whitespace_not_flagged_for_space_indented_closing_bracket() -> None:
    """Space indentation before standalone ')' is not bracket_whitespace."""
    code = "x = foo(\n    1,\n    2,\n    )\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "bracket_whitespace" for f in findings)


# ---------------------------------------------------------------------------
# whitespace_before_punctuation (E203)
# ---------------------------------------------------------------------------


# TC-ANALYSIS-105
def test_whitespace_before_punctuation_detected() -> None:
    """Space before comma is flagged."""
    code = "x = [1 , 2]\n"
    findings, _ = run_static_analysis(code)
    wp = [f for f in findings if f.issue_type == "whitespace_before_punctuation"]
    assert len(wp) >= 1


# TC-ANALYSIS-106
def test_whitespace_before_punctuation_not_flagged() -> None:
    """No space before comma is not flagged."""
    code = "x = [1, 2]\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "whitespace_before_punctuation" for f in findings)


# ---------------------------------------------------------------------------
# whitespace_before_call (E211)
# ---------------------------------------------------------------------------


# TC-ANALYSIS-106
def test_whitespace_before_call_detected() -> None:
    """Space before opening paren in call is flagged."""
    code = "def foo():\n" '    """Doc."""\n' "    bar (1)\n"
    findings, _ = run_static_analysis(code)
    wbc = [f for f in findings if f.issue_type == "whitespace_before_call"]
    assert len(wbc) >= 1


# TC-ANALYSIS-107
def test_whitespace_before_call_not_flagged() -> None:
    """No space before paren in call is not flagged."""
    code = "def foo():\n" '    """Doc."""\n' "    bar(1)\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "whitespace_before_call" for f in findings)


# ---------------------------------------------------------------------------
# whitespace_after_separator (E231)
# ---------------------------------------------------------------------------


# TC-ANALYSIS-108
def test_whitespace_after_separator_detected() -> None:
    """Missing space after comma is flagged."""
    code = "x = [1,2,3]\n"
    findings, _ = run_static_analysis(code)
    was = [f for f in findings if f.issue_type == "whitespace_after_separator"]
    assert len(was) >= 1


# TC-ANALYSIS-109
def test_whitespace_after_separator_not_flagged() -> None:
    """Space after comma is not flagged."""
    code = "x = [1, 2, 3]\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "whitespace_after_separator" for f in findings)


# ---------------------------------------------------------------------------
# operator_spacing (E225)
# ---------------------------------------------------------------------------


# TC-ANALYSIS-110
def test_operator_spacing_detected() -> None:
    """Missing space around = is flagged (not in def/lambda)."""
    code = "x=1\n"
    findings, _ = run_static_analysis(code)
    ops = [f for f in findings if f.issue_type == "operator_spacing"]
    assert len(ops) >= 1
    assert ops[0].column_start == 2
    assert ops[0].column_end == 2


# TC-ANALYSIS-110A
def test_operator_spacing_detected_missing_right_side_space() -> None:
    """Missing right-side space around = is flagged."""
    code = "x =1\n"
    findings, _ = run_static_analysis(code)
    ops = [f for f in findings if f.issue_type == "operator_spacing"]
    assert len(ops) >= 1


# TC-ANALYSIS-111
def test_operator_spacing_not_flagged_for_spaced() -> None:
    """Properly spaced = is not flagged."""
    code = "x = 1\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "operator_spacing" for f in findings)


# TC-ANALYSIS-112
def test_operator_spacing_not_flagged_for_keyword_argument() -> None:
    """Keyword arguments such as default_factory=list are not flagged."""
    code = "from dataclasses import field\n\nvalue = field(default_factory=list)\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "operator_spacing" for f in findings)


# ---------------------------------------------------------------------------
# keyword_arg_spacing (E251)
# ---------------------------------------------------------------------------


# TC-ANALYSIS-113
def test_keyword_arg_spacing_detected() -> None:
    """Space around = in default param is flagged."""
    code = 'def foo(x = 1):\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    kas = [f for f in findings if f.issue_type == "keyword_arg_spacing"]
    assert len(kas) == 1


# TC-ANALYSIS-114
def test_keyword_arg_spacing_not_flagged() -> None:
    """No space around = in default param is not flagged."""
    code = 'def foo(x=1):\n    """Doc."""\n    pass\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "keyword_arg_spacing" for f in findings)


# TC-ANALYSIS-114A
def test_keyword_arg_spacing_detected_for_call_keyword_spaces() -> None:
    """Spaces around = in call keyword argument are flagged."""
    code = "result = magic(r = 1)\n"
    findings, _ = run_static_analysis(code)
    kas = [f for f in findings if f.issue_type == "keyword_arg_spacing"]
    assert len(kas) >= 1
    assert kas[0].column_start is not None


# TC-ANALYSIS-114B
def test_keyword_arg_spacing_not_flagged_for_annotated_default_with_spaces() -> None:
    """Annotated defaults require spaces around = and should pass."""
    code = 'def foo(x: int = 1):\n    """Doc."""\n    return x\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "keyword_arg_spacing" for f in findings)


# TC-ANALYSIS-114C
def test_keyword_arg_spacing_detected_for_annotated_default_without_spaces() -> None:
    """Annotated defaults without spaces around = are flagged."""
    code = 'def foo(x: int=1):\n    """Doc."""\n    return x\n'
    findings, _ = run_static_analysis(code)
    kas = [f for f in findings if f.issue_type == "keyword_arg_spacing"]
    assert len(kas) >= 1


# ---------------------------------------------------------------------------
# binary_operator_line_break (W504)
# ---------------------------------------------------------------------------


# TC-ANALYSIS-115
def test_binary_operator_line_break_detected() -> None:
    """Line ending with 'and' operator is flagged."""
    code = "def foo():\n" '    """Doc."""\n' "    x = (a and\n" "         b)\n"
    findings, _ = run_static_analysis(code)
    bolb = [f for f in findings if f.issue_type == "binary_operator_line_break"]
    assert len(bolb) >= 1


# TC-ANALYSIS-115
def test_binary_operator_line_break_not_flagged() -> None:
    """Line breaking before 'and' is not flagged."""
    code = "def foo():\n" '    """Doc."""\n' "    x = (a\n" "         and b)\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "binary_operator_line_break" for f in findings)


# ---------------------------------------------------------------------------
# arrow_spacing
# ---------------------------------------------------------------------------


# TC-ANALYSIS-116
def test_arrow_spacing_detected() -> None:
    """Missing space around -> is flagged."""
    code = 'def foo()->int:\n    """Doc."""\n    return 1\n'
    findings, _ = run_static_analysis(code)
    ar = [f for f in findings if f.issue_type == "arrow_spacing"]
    assert len(ar) == 1


# TC-ANALYSIS-117
def test_arrow_spacing_not_flagged() -> None:
    """Properly spaced -> is not flagged."""
    code = 'def foo() -> int:\n    """Doc."""\n    return 1\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "arrow_spacing" for f in findings)


# ---------------------------------------------------------------------------
# annotation_spacing
# ---------------------------------------------------------------------------


# TC-ANALYSIS-118
def test_annotation_spacing_detected() -> None:
    """Missing space after : in annotation is flagged."""
    code = "x:int = 1\n"
    findings, _ = run_static_analysis(code)
    ans = [f for f in findings if f.issue_type == "annotation_spacing"]
    assert len(ans) == 1


# TC-ANALYSIS-119
def test_annotation_spacing_not_flagged() -> None:
    """Properly spaced annotation is not flagged."""
    code = "x: int = 1\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "annotation_spacing" for f in findings)


# TC-ANALYSIS-119A
def test_annotation_spacing_detected_space_before_colon() -> None:
    """Space before ':' in annotation is flagged."""
    code = "x : int = 1\n"
    findings, _ = run_static_analysis(code)
    ans = [f for f in findings if f.issue_type == "annotation_spacing"]
    assert len(ans) == 1


# TC-ANALYSIS-119B
def test_annotation_spacing_not_flagged_for_named_slice() -> None:
    """Named slices (a:b) are not misclassified as annotations."""
    code = "x = arr[a:b]\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "annotation_spacing" for f in findings)


# TC-ANALYSIS-119C
def test_annotation_spacing_detected_for_function_parameter_annotation() -> None:
    """Missing space after ':' in function parameter annotation is flagged."""
    code = 'def foo(x:int):\n    """Doc."""\n    return x\n'
    findings, _ = run_static_analysis(code)
    ans = [f for f in findings if f.issue_type == "annotation_spacing"]
    assert len(ans) == 1
    assert ans[0].column_start is not None


# TC-ANALYSIS-119D
def test_operator_spacing_parity_with_pycodestyle_e225() -> None:
    """Assignment spacing tracks pycodestyle E225 outcomes."""
    cases = (
        ("x = 1\n", False),
        ("x=1\n", True),
        ("x =1\n", True),
    )
    for code, expected in cases:
        findings, _ = run_static_analysis(code)
        has_engine_issue = any(f.issue_type == "operator_spacing" for f in findings)
        has_pycodestyle_issue = "E225" in _pycodestyle_codes(code)
        assert has_engine_issue == expected
        assert has_engine_issue == has_pycodestyle_issue


# TC-ANALYSIS-119E
def test_keyword_arg_spacing_parity_with_pycodestyle() -> None:
    """Keyword/default spacing tracks pycodestyle E251/E252 outcomes."""
    cases = (
        ("value = f(a=1)\n", False),
        ("value = f(a = 1)\n", True),
        ('def f(x=1):\n    """Doc."""\n    return x\n', False),
        ('def f(x = 1):\n    """Doc."""\n    return x\n', True),
        ('def f(x: int = 1):\n    """Doc."""\n    return x\n', False),
        ('def f(x: int=1):\n    """Doc."""\n    return x\n', True),
    )
    for code, expected in cases:
        findings, _ = run_static_analysis(code)
        has_engine_issue = any(f.issue_type == "keyword_arg_spacing" for f in findings)
        py_codes = _pycodestyle_codes(code)
        has_pycodestyle_issue = bool(py_codes.intersection({"E251", "E252"}))
        assert has_engine_issue == expected
        assert has_engine_issue == has_pycodestyle_issue


# TC-ANALYSIS-119F
def test_annotation_spacing_parity_with_pycodestyle_e231() -> None:
    """Annotation spacing tracks pycodestyle and ignores named slices."""
    cases = (
        ("x: int = 1\n", False),
        ("x:int = 1\n", True),
        ('def f(x: int):\n    """Doc."""\n    return x\n', False),
        ('def f(x:int):\n    """Doc."""\n    return x\n', True),
        ("x = arr[a:b]\n", False),
    )
    for code, expected in cases:
        findings, _ = run_static_analysis(code)
        has_engine_issue = any(f.issue_type == "annotation_spacing" for f in findings)
        has_pycodestyle_issue = "E231" in _pycodestyle_codes(code)
        assert has_engine_issue == expected
        assert has_engine_issue == has_pycodestyle_issue


# ---------------------------------------------------------------------------
# block_comment_capitalization
# ---------------------------------------------------------------------------


# TC-ANALYSIS-120
def test_block_comment_capitalization_detected() -> None:
    """A block comment starting with a lowercase word is flagged."""
    code = "# this is a comment\nx = 1\n"
    findings, _ = run_static_analysis(code)
    bcc = [f for f in findings if f.issue_type == "block_comment_capitalization"]
    assert len(bcc) == 1


# TC-ANALYSIS-121
def test_block_comment_capitalization_not_flagged() -> None:
    """A block comment starting with an uppercase word is not flagged."""
    code = "# This is a comment\nx = 1\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "block_comment_capitalization" for f in findings)


# ---------------------------------------------------------------------------
# block_comment_indentation
# ---------------------------------------------------------------------------


# TC-ANALYSIS-122
def test_block_comment_indentation_detected() -> None:
    """A block comment misaligned with the following code is flagged."""
    code = "def foo():\n" '    """Doc."""\n' "# Misaligned comment\n" "    x = 1\n"
    findings, _ = run_static_analysis(code)
    bci = [f for f in findings if f.issue_type == "block_comment_indentation"]
    assert len(bci) >= 1


# TC-ANALYSIS-123
def test_block_comment_indentation_not_flagged() -> None:
    """A block comment aligned with the following code is not flagged."""
    code = "def foo():\n" '    """Doc."""\n' "    # Aligned comment\n" "    x = 1\n"
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "block_comment_indentation" for f in findings)


# ---------------------------------------------------------------------------
# quote_consistency
# ---------------------------------------------------------------------------


# TC-ANALYSIS-124
def test_quote_consistency_detected() -> None:
    """Minority quote style in a predominantly double-quoted file is flagged."""
    code = 'x = "hello"\n' 'y = "world"\n' 'z = "foo"\n' 'a = "bar"\n' "w = 'odd'\n"
    findings, _ = run_static_analysis(code)
    qc = [f for f in findings if f.issue_type == "quote_consistency"]
    assert len(qc) >= 1


# TC-ANALYSIS-125
def test_quote_consistency_not_flagged() -> None:
    """A file with consistent quote style is not flagged."""
    code = 'x = "hello"\ny = "world"\n'
    findings, _ = run_static_analysis(code)
    assert not any(f.issue_type == "quote_consistency" for f in findings)


# ---------------------------------------------------------------------------
# module_naming
# ---------------------------------------------------------------------------


# TC-ANALYSIS-126
def test_module_naming_detected() -> None:
    """A non-lowercase module filename is flagged."""
    code = "x = 1\n"
    findings, _ = run_static_analysis(code, filename="MyModule.py")
    mn = [f for f in findings if f.issue_type == "module_naming"]
    assert len(mn) == 1


# TC-ANALYSIS-127
def test_module_naming_not_flagged() -> None:
    """A lowercase module filename is not flagged."""
    code = "x = 1\n"
    findings, _ = run_static_analysis(code, filename="my_module.py")
    assert not any(f.issue_type == "module_naming" for f in findings)
