"""Unit tests for the static analysis engine."""

from app.models.analysis import Finding, PredictedBug
from app.services.analysis_engine import compute_score, run_static_analysis


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
