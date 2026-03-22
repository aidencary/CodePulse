"""Static analysis engine — AST-based code quality checks for Python submissions."""

import ast
import logging
import re

from app.models.analysis import Finding, PredictedBug

logger = logging.getLogger(__name__)

_LONG_LINE_LIMIT = 88
_DUNDER_METHODS = frozenset(
    {
        "__init__",
        "__str__",
        "__repr__",
        "__len__",
        "__eq__",
        "__hash__",
        "__lt__",
        "__le__",
        "__gt__",
        "__ge__",
        "__enter__",
        "__exit__",
        "__iter__",
        "__next__",
        "__getitem__",
        "__setitem__",
        "__delitem__",
        "__contains__",
        "__call__",
        "__del__",
        "__new__",
    }
)
_AMBIGUOUS_NAMES = frozenset({"l", "O", "I"})

_SEVERITY_PENALTIES: dict[str, int] = {
    # static findings
    "High": 10,
    "Med": 5,
    "Low": 2,
    # predicted bugs
    "critical": 8,
    "high": 4,
    "medium": 2,
    "low": 1,
}


# ---------------------------------------------------------------------------
# Naming helpers
# ---------------------------------------------------------------------------


def _is_camel_case(name: str) -> bool:
    """Return True if *name* uses camelCase (lowercase start, uppercase inside)."""
    stripped = name.lstrip("_")
    if not stripped:
        return False
    return bool(re.match(r"^[a-z]", stripped) and re.search(r"[A-Z]", stripped))


def _is_pascal_case(name: str) -> bool:
    """Return True if *name* uses PascalCase (CapWords)."""
    stripped = name.lstrip("_")
    if not stripped:
        return True
    return stripped[0].isupper() and "_" not in stripped


def _is_snake_case(name: str) -> bool:
    """Return True if *name* uses snake_case."""
    stripped = name.lstrip("_")
    if not stripped:
        return True
    return bool(re.match(r"^[a-z][a-z0-9_]*$", stripped))


def _is_upper_snake_case(name: str) -> bool:
    """Return True if *name* uses UPPER_SNAKE_CASE."""
    stripped = name.lstrip("_")
    if not stripped:
        return True
    return bool(re.match(r"^[A-Z][A-Z0-9_]*$", stripped))


# ---------------------------------------------------------------------------
# AST node helpers
# ---------------------------------------------------------------------------


def _is_none_const(node: ast.expr) -> bool:
    """Return True if *node* is the ``None`` constant."""
    return isinstance(node, ast.Constant) and node.value is None


def _is_bool_const(node: ast.expr) -> bool:
    """Return True if *node* is ``True`` or ``False``."""
    return isinstance(node, ast.Constant) and isinstance(node.value, bool)


def _is_type_call(node: ast.expr) -> bool:
    """Return True if *node* is a ``type(...)`` call."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "type"
    )


def _is_len_call(node: ast.expr) -> bool:
    """Return True if *node* is a ``len(...)`` call."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "len"
    )


def _is_zero_const(node: ast.expr) -> bool:
    """Return True if *node* is the integer ``0``."""
    return (
        isinstance(node, ast.Constant)
        and node.value == 0
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
    )


def _is_string_slice(node: ast.expr) -> bool:
    """Return True if *node* is a subscript with a slice (e.g., ``s[:3]``)."""
    return isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice)


def _suggest_string_method(node: ast.Subscript) -> str | None:
    """Return ``'startswith'`` or ``'endswith'`` based on the slice pattern."""
    sl = node.slice
    if not isinstance(sl, ast.Slice) or sl.step is not None:
        return None
    if sl.lower is None and sl.upper is not None:
        return "startswith"
    if sl.lower is not None and sl.upper is None:
        if isinstance(sl.lower, ast.UnaryOp) and isinstance(sl.lower.op, ast.USub):
            return "endswith"
    return None


def _collect_returns(node: ast.AST) -> list[ast.Return]:
    """Collect Return nodes in *node*, skipping nested function definitions."""
    returns: list[ast.Return] = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.Return):
            returns.append(child)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        else:
            returns.extend(_collect_returns(child))
    return returns


# ---------------------------------------------------------------------------
# Private check functions
# ---------------------------------------------------------------------------


def _check_long_lines(code: str) -> list[Finding]:
    """Return a Finding for each line that exceeds the 88-character limit."""
    findings: list[Finding] = []
    for line_number, line in enumerate(code.splitlines(), start=1):
        if len(line) > _LONG_LINE_LIMIT:
            findings.append(
                Finding(
                    issue_type="long_line",
                    line_number=line_number,
                    severity="Low",
                    message=(
                        f"Line exceeds {_LONG_LINE_LIMIT} characters "
                        f"({len(line)} chars)."
                    ),
                )
            )
    return findings


def _check_missing_docstrings(tree: ast.Module) -> list[Finding]:
    """Return a Finding for every function or class missing a docstring."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        # Skip dunder methods — intentionally undocumented in most styles.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in _DUNDER_METHODS:
                continue
        if ast.get_docstring(node) is None:
            kind = "Class" if isinstance(node, ast.ClassDef) else "Function"
            findings.append(
                Finding(
                    issue_type="missing_docstring",
                    line_number=node.lineno,
                    severity="Low",
                    message=f"{kind} '{node.name}' is missing a docstring.",
                )
            )
    return findings


def _check_bare_excepts(tree: ast.Module) -> list[Finding]:
    """Return a Finding for each bare ``except:`` clause."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            findings.append(
                Finding(
                    issue_type="bare_except",
                    line_number=node.lineno,
                    severity="Med",
                    message=(
                        "Bare 'except:' catches all exceptions including "
                        "SystemExit and KeyboardInterrupt. "
                        "Use 'except Exception:' instead."
                    ),
                )
            )
    return findings


def _check_naming_conventions(tree: ast.Module) -> list[Finding]:
    """Check naming conventions per PEP 8.

    Detects camelCase functions/variables, non-PascalCase classes,
    non-UPPER_SNAKE_CASE module-level constants, and ambiguous
    single-character names (l, O, I).
    """
    findings: list[Finding] = []
    flagged_names: set[str] = set()

    for node in ast.walk(tree):
        # Functions/methods: should be snake_case, not camelCase.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("__") and _is_camel_case(node.name):
                findings.append(
                    Finding(
                        issue_type="naming_convention",
                        line_number=node.lineno,
                        severity="Low",
                        message=(
                            f"Function '{node.name}' uses camelCase. "
                            f"Use snake_case instead."
                        ),
                    )
                )

        # Classes: should be PascalCase (CapWords).
        if isinstance(node, ast.ClassDef):
            if not _is_pascal_case(node.name):
                findings.append(
                    Finding(
                        issue_type="naming_convention",
                        line_number=node.lineno,
                        severity="Low",
                        message=(
                            f"Class '{node.name}' should use " f"PascalCase (CapWords)."
                        ),
                    )
                )

        # Variables: flag ambiguous names and camelCase (deduplicated).
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if node.id in flagged_names:
                continue
            if node.id in _AMBIGUOUS_NAMES:
                flagged_names.add(node.id)
                findings.append(
                    Finding(
                        issue_type="ambiguous_name",
                        line_number=node.lineno,
                        severity="Med",
                        message=(
                            f"Ambiguous variable name '{node.id}'. "
                            f"Avoid 'l', 'O', and 'I' as they "
                            f"resemble digits or pipes."
                        ),
                    )
                )
            elif _is_camel_case(node.id):
                flagged_names.add(node.id)
                findings.append(
                    Finding(
                        issue_type="naming_convention",
                        line_number=node.lineno,
                        severity="Low",
                        message=(
                            f"Variable '{node.id}' uses camelCase. "
                            f"Use snake_case instead."
                        ),
                    )
                )

    # Module-level constants: literal values should use UPPER_SNAKE_CASE.
    for stmt in tree.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if not isinstance(stmt.value, ast.Constant):
            continue
        for target in stmt.targets:
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            if name.startswith("__"):
                continue
            # Skip names already caught by the camelCase variable check.
            if _is_camel_case(name):
                continue
            if not _is_snake_case(name) and not _is_upper_snake_case(name):
                findings.append(
                    Finding(
                        issue_type="naming_convention",
                        line_number=stmt.lineno,
                        severity="Low",
                        message=(
                            f"Module-level constant '{name}' should "
                            f"use UPPER_SNAKE_CASE."
                        ),
                    )
                )

    return findings


def _check_self_cls(tree: ast.Module) -> list[Finding]:
    """Verify instance methods use ``self`` and classmethods use ``cls``."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decorator_names = {
                d.id for d in item.decorator_list if isinstance(d, ast.Name)
            }
            if "staticmethod" in decorator_names:
                continue
            if not item.args.args:
                continue
            first_arg = item.args.args[0].arg
            if "classmethod" in decorator_names:
                if first_arg != "cls":
                    findings.append(
                        Finding(
                            issue_type="self_cls_naming",
                            line_number=item.lineno,
                            severity="Med",
                            message=(
                                f"Class method '{item.name}' should "
                                f"use 'cls' as first parameter, "
                                f"not '{first_arg}'."
                            ),
                        )
                    )
            else:
                if first_arg != "self":
                    findings.append(
                        Finding(
                            issue_type="self_cls_naming",
                            line_number=item.lineno,
                            severity="Med",
                            message=(
                                f"Instance method '{item.name}' "
                                f"should use 'self' as first "
                                f"parameter, not '{first_arg}'."
                            ),
                        )
                    )
    return findings


def _check_none_comparison(tree: ast.Module) -> list[Finding]:
    """Flag ``== None`` and ``!= None`` — should use ``is``/``is not``."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        all_values = [node.left] + node.comparators
        for i, op in enumerate(node.ops):
            if not isinstance(op, (ast.Eq, ast.NotEq)):
                continue
            left = all_values[i]
            right = all_values[i + 1]
            if _is_none_const(left) or _is_none_const(right):
                findings.append(
                    Finding(
                        issue_type="none_comparison",
                        line_number=node.lineno,
                        severity="Med",
                        message=(
                            "Use 'is None' or 'is not None' instead "
                            "of '== None' or '!= None'."
                        ),
                    )
                )
                break
    return findings


def _check_boolean_comparison(tree: ast.Module) -> list[Finding]:
    """Flag comparisons to ``True`` or ``False`` with ``==``/``is``."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        all_values = [node.left] + node.comparators
        for i, op in enumerate(node.ops):
            if not isinstance(op, (ast.Eq, ast.NotEq, ast.Is, ast.IsNot)):
                continue
            left = all_values[i]
            right = all_values[i + 1]
            if _is_bool_const(left) or _is_bool_const(right):
                findings.append(
                    Finding(
                        issue_type="boolean_comparison",
                        line_number=node.lineno,
                        severity="Low",
                        message=(
                            "Don't compare to True or False. Use the "
                            "value directly or the 'not' operator."
                        ),
                    )
                )
                break
    return findings


def _check_type_comparison(tree: ast.Module) -> list[Finding]:
    """Flag ``type(x) is type(y)`` — should use ``isinstance()``."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        all_values = [node.left] + node.comparators
        for i, op in enumerate(node.ops):
            if not isinstance(op, (ast.Is, ast.IsNot, ast.Eq, ast.NotEq)):
                continue
            left = all_values[i]
            right = all_values[i + 1]
            if _is_type_call(left) and _is_type_call(right):
                findings.append(
                    Finding(
                        issue_type="type_comparison",
                        line_number=node.lineno,
                        severity="Med",
                        message=(
                            "Use isinstance() instead of comparing " "types directly."
                        ),
                    )
                )
                break
    return findings


def _check_empty_sequence(tree: ast.Module) -> list[Finding]:
    """Flag ``len(seq) == 0`` — should use truthiness instead."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        all_values = [node.left] + node.comparators
        for i, op in enumerate(node.ops):
            if not isinstance(
                op, (ast.Eq, ast.NotEq, ast.Gt, ast.Lt, ast.GtE, ast.LtE)
            ):
                continue
            left = all_values[i]
            right = all_values[i + 1]
            if (_is_len_call(left) and _is_zero_const(right)) or (
                _is_zero_const(left) and _is_len_call(right)
            ):
                findings.append(
                    Finding(
                        issue_type="empty_sequence_check",
                        line_number=node.lineno,
                        severity="Low",
                        message=(
                            "Use truthiness to check for empty "
                            "sequences (e.g., 'if seq:' or "
                            "'if not seq:') instead of len()."
                        ),
                    )
                )
                break
    return findings


def _check_lambda_assignment(tree: ast.Module) -> list[Finding]:
    """Flag ``x = lambda ...`` — should use ``def`` instead."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Lambda):
            findings.append(
                Finding(
                    issue_type="lambda_assignment",
                    line_number=node.lineno,
                    severity="Low",
                    message=(
                        "Do not assign a lambda expression to a "
                        "variable. Use 'def' instead."
                    ),
                )
            )
    return findings


def _check_import_formatting(tree: ast.Module) -> list[Finding]:
    """Flag ``import os, sys`` — each import should be on a separate line."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and len(node.names) > 1:
            names = ", ".join(alias.name for alias in node.names)
            findings.append(
                Finding(
                    issue_type="import_formatting",
                    line_number=node.lineno,
                    severity="Low",
                    message=(
                        f"Multiple imports on one line "
                        f"('import {names}'). "
                        f"Put each import on a separate line."
                    ),
                )
            )
    return findings


def _check_is_not_preference(tree: ast.Module) -> list[Finding]:
    """Flag ``not x is y`` — should use ``x is not y``."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.UnaryOp)
            and isinstance(node.op, ast.Not)
            and isinstance(node.operand, ast.Compare)
            and len(node.operand.ops) == 1
            and isinstance(node.operand.ops[0], ast.Is)
        ):
            findings.append(
                Finding(
                    issue_type="is_not_preference",
                    line_number=node.lineno,
                    severity="Low",
                    message="Use 'is not' instead of 'not ... is'.",
                )
            )
    return findings


def _check_return_consistency(tree: ast.Module) -> list[Finding]:
    """Flag functions with mixed explicit return values and bare returns."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        returns = _collect_returns(node)
        if not returns:
            continue
        has_value = any(r.value is not None for r in returns)
        has_bare = any(r.value is None for r in returns)
        if has_value and has_bare:
            findings.append(
                Finding(
                    issue_type="return_consistency",
                    line_number=node.lineno,
                    severity="Med",
                    message=(
                        f"Function '{node.name}' has inconsistent "
                        f"return statements. All returns should "
                        f"either return a value or return None."
                    ),
                )
            )
    return findings


def _check_exception_inheritance(tree: ast.Module) -> list[Finding]:
    """Flag classes inheriting directly from ``BaseException``."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "BaseException":
                findings.append(
                    Finding(
                        issue_type="exception_inheritance",
                        line_number=node.lineno,
                        severity="Med",
                        message=(
                            f"Class '{node.name}' inherits from "
                            f"BaseException. Derive from Exception "
                            f"instead."
                        ),
                    )
                )
    return findings


def _check_string_slicing(tree: ast.Module) -> list[Finding]:
    """Flag ``s[:n] == 'prefix'`` — use ``.startswith()``/``.endswith()``."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        all_values = [node.left] + node.comparators
        for i, op in enumerate(node.ops):
            if not isinstance(op, (ast.Eq, ast.NotEq)):
                continue
            left = all_values[i]
            right = all_values[i + 1]
            method = None
            if _is_string_slice(left) and isinstance(right, ast.Constant):
                if isinstance(right.value, str):
                    method = _suggest_string_method(left)
            elif _is_string_slice(right) and isinstance(left, ast.Constant):
                if isinstance(left.value, str):
                    method = _suggest_string_method(right)
            if method:
                findings.append(
                    Finding(
                        issue_type="string_slicing",
                        line_number=node.lineno,
                        severity="Low",
                        message=(
                            f"Use '.{method}()' instead of string "
                            f"slicing for prefix/suffix checks."
                        ),
                    )
                )
                break
    return findings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_score(
    findings: list[Finding],
    predicted_bugs: list[PredictedBug],
) -> int:
    """Compute an overall quality score (0–100) from findings and predicted bugs.

    Args:
        findings: Static analysis findings with Low / Med / High severity.
        predicted_bugs: GPT-predicted bugs with low / medium / high / critical severity.

    Returns:
        An integer score between 0 and 100 inclusive.
    """
    penalty = 0
    for f in findings:
        penalty += _SEVERITY_PENALTIES.get(f.severity, 0)
    for b in predicted_bugs:
        penalty += _SEVERITY_PENALTIES.get(b.severity, 0)
    return max(0, 100 - penalty)


def run_static_analysis(code: str) -> tuple[list[Finding], int]:
    """Run all static checks against *code* and return findings with a raw score.

    The returned score is based on static findings only.  The caller should
    invoke :func:`compute_score` again once GPT predictions are available to
    produce the final score.

    Args:
        code: The Python source code string to analyse.

    Returns:
        A tuple of ``(findings, raw_score)`` where *raw_score* is computed
        from static findings alone.
    """
    findings: list[Finding] = []

    # Parse — catch syntax errors before attempting AST traversal.
    tree: ast.Module | None = None
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        findings.append(
            Finding(
                issue_type="syntax_error",
                line_number=exc.lineno or 1,
                severity="High",
                message=f"Syntax error: {exc.msg}.",
            )
        )
        raw_score = compute_score(findings, [])
        return findings, raw_score

    # Text-based checks.
    findings.extend(_check_long_lines(code))

    # AST-based checks.
    findings.extend(_check_missing_docstrings(tree))
    findings.extend(_check_bare_excepts(tree))
    findings.extend(_check_naming_conventions(tree))
    findings.extend(_check_self_cls(tree))
    findings.extend(_check_none_comparison(tree))
    findings.extend(_check_boolean_comparison(tree))
    findings.extend(_check_type_comparison(tree))
    findings.extend(_check_empty_sequence(tree))
    findings.extend(_check_lambda_assignment(tree))
    findings.extend(_check_import_formatting(tree))
    findings.extend(_check_is_not_preference(tree))
    findings.extend(_check_return_consistency(tree))
    findings.extend(_check_exception_inheritance(tree))
    findings.extend(_check_string_slicing(tree))

    raw_score = compute_score(findings, [])
    logger.debug(
        "Static analysis complete: %d findings, raw score %d",
        len(findings),
        raw_score,
    )
    return findings, raw_score
