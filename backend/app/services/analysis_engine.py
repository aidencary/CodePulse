"""Static analysis engine — AST-based code quality checks for Python submissions."""

import ast
import logging
from typing import Union

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


'''
Private Helper Methods:
These methods implement individual static analysis checks.  
They are not intended to be called directly by external code.
Instead, they are invoked by the public API methods defined below.

Method Names:
- _check_long_lines, _check_missing_docstrings, and _check_bare_excepts each return a list of Findings for the specific issue they check for.
- _check_missing_docstrings takes the pre-parsed AST as an argument to avoid redundant parsing and allow for more efficient analysis.
- _check_bare_excepts also relies on the AST to identify except clauses and determine if they are bare (i.e., have no specified exception type).
'''


def _check_long_lines(code: str) -> list[Finding]:
    """Return a Finding for each line that exceeds the 88-character limit."""
    findings: list[Finding] = []
    # Note: we check line lengths against the raw code string rather than the AST
    # because the AST doesn't preserve formatting details like line breaks or indentation.
    for line_number, line in enumerate(code.splitlines(), start=1):
        # We use a limit of 88 chars (the PEP 8 limit) to allow for indentation and avoid false positives.
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


def _check_missing_docstrings(
    # Create the AST from the code string once and pass it to this function.
    tree: ast.Module,
) -> list[Finding]:
    """Return a Finding for every function or class missing a docstring."""
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            continue
        # Skip dunder methods (e.g., __init__) — they are intentionally undocumented in most styles.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in _DUNDER_METHODS:
                continue
        # The AST doesn't preserve comments or docstrings as separate nodes,
        #  so we have to check for missing docstrings by looking at function and class definitions
        if ast.get_docstring(node) is None:
            kind = "Class" if isinstance(node, ast.ClassDef) else "Function"
            findings.append(
                Finding(
                    issue_type="missing_docstring",
                    line_number=node.lineno,
                    severity="Low",
                    message=(
                        f"{kind} '{node.name}' is missing a docstring."
                    ),
                )
            )
    return findings


def _check_bare_excepts(tree: ast.Module) -> list[Finding]:
    """Return a Finding for each bare ``except:`` clause."""
    findings: list[Finding] = []
    # The AST represents both ``except:`` and ``except Exception:`` as ExceptHandler nodes,
    # but the former has a None type while the latter has a non-None type.
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


'''
Public API Methods:
These methods are intended to be called by external code (e.g., API endpoints) to perform analysis tasks.
They provide a clean interface for running static analysis and computing overall scores based on findings and predicted bugs.

Method Names:
- compute_score: Computes an overall quality score (0-100) from static analysis findings and GPT-predicted bugs.
                 It takes lists of Findings and PredictedBugs as input and applies severity-based penalties to calculate the final score.
- run_static_analysis: Runs all static checks against a given code string and returns a tuple of (findings, raw_score).
                       The raw_score is computed from static findings alone and can be used as a baseline before incorporating GPT predictions.
'''

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
    tree: Union[ast.Module, None] = None
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

    # Run individual checks.
    findings.extend(_check_long_lines(code))
    findings.extend(_check_missing_docstrings(tree))
    findings.extend(_check_bare_excepts(tree))

    raw_score = compute_score(findings, [])
    logger.debug("Static analysis complete: %d findings, raw score %d", len(findings), raw_score)
    return findings, raw_score