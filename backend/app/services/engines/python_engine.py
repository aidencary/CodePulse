""" v1.0.0 Python static analysis engine — single-pass AST and text-based PEP 8 checks."""

import ast
import logging
import re
import sys

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

_TRY_BLOCK_LIMIT = 5

# Expanded set of recognised Python dunder methods (for invalid_dunder check).
_RECOGNIZED_DUNDERS = frozenset(
    {
        # Object basics
        "__init__",
        "__new__",
        "__del__",
        "__repr__",
        "__str__",
        "__bytes__",
        "__format__",
        "__hash__",
        "__bool__",
        "__sizeof__",
        # Rich comparison
        "__lt__",
        "__le__",
        "__eq__",
        "__ne__",
        "__gt__",
        "__ge__",
        # Attribute access
        "__getattr__",
        "__getattribute__",
        "__setattr__",
        "__delattr__",
        "__dir__",
        # Descriptor protocol
        "__get__",
        "__set__",
        "__delete__",
        "__set_name__",
        # Class creation
        "__init_subclass__",
        "__prepare__",
        "__class_getitem__",
        "__instancecheck__",
        "__subclasscheck__",
        # Container
        "__len__",
        "__length_hint__",
        "__getitem__",
        "__setitem__",
        "__delitem__",
        "__missing__",
        "__iter__",
        "__reversed__",
        "__contains__",
        # Numeric — unary
        "__neg__",
        "__pos__",
        "__abs__",
        "__invert__",
        "__complex__",
        "__int__",
        "__float__",
        "__index__",
        "__round__",
        "__trunc__",
        "__floor__",
        "__ceil__",
        # Numeric — binary
        "__add__",
        "__radd__",
        "__iadd__",
        "__sub__",
        "__rsub__",
        "__isub__",
        "__mul__",
        "__rmul__",
        "__imul__",
        "__truediv__",
        "__rtruediv__",
        "__itruediv__",
        "__floordiv__",
        "__rfloordiv__",
        "__ifloordiv__",
        "__mod__",
        "__rmod__",
        "__imod__",
        "__divmod__",
        "__rdivmod__",
        "__pow__",
        "__rpow__",
        "__ipow__",
        "__lshift__",
        "__rlshift__",
        "__ilshift__",
        "__rshift__",
        "__rrshift__",
        "__irshift__",
        "__and__",
        "__rand__",
        "__iand__",
        "__xor__",
        "__rxor__",
        "__ixor__",
        "__or__",
        "__ror__",
        "__ior__",
        "__matmul__",
        "__rmatmul__",
        "__imatmul__",
        # Context manager
        "__enter__",
        "__exit__",
        "__aenter__",
        "__aexit__",
        # Callable
        "__call__",
        # Iteration / async
        "__next__",
        "__await__",
        "__aiter__",
        "__anext__",
        # Pickling / copying
        "__copy__",
        "__deepcopy__",
        "__reduce__",
        "__reduce_ex__",
        "__getnewargs__",
        "__getnewargs_ex__",
        "__getstate__",
        "__setstate__",
        # Filesystem
        "__fspath__",
        # Module-level
        "__slots__",
    }
)

# Module-level dunder names that must come before imports.
_MODULE_DUNDERS = frozenset(
    {"__all__", "__author__", "__version__", "__email__", "__license__"}
)

# Keywords that introduce compound statements.
_COMPOUND_KEYWORDS = frozenset(
    {"if", "elif", "else", "for", "while", "with", "try", "except", "finally"}
)

# Binary operators that should break before the operator, not after.
_BINARY_OPS = frozenset(
    {"+", "-", "*", "/", "//", "%", "**", "and", "or", "|", "&", "^"}
)

# Known top-level local packages for absolute-import grouping.
_LOCAL_IMPORT_ROOTS = frozenset({"app"})

# Comment prefixes to skip for block-comment capitalisation check.
_COMMENT_SKIP_PREFIXES = (
    "#!",
    "# noqa",
    "# type:",
    "# TODO",
    "# FIXME",
    "# XXX",
    "# pylint",
    "# pragma",
    "# FR-",
    "# TC-",
    "# NFR-",
)


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


def _find_comment_start(line: str) -> int | None:
    """Return the index of ``#`` that starts a comment, skipping strings."""
    in_single = False
    in_double = False
    i = 0
    while i < len(line):
        c = line[i]
        if c == "\\" and (in_single or in_double):
            i += 2
            continue
        if c == "'" and not in_double:
            in_single = not in_single
        elif c == '"' and not in_single:
            in_double = not in_double
        elif c == "#" and not in_single and not in_double:
            return i
        i += 1
    return None


def _effective_start(node: ast.AST) -> int:
    """Return the first line of *node*, accounting for decorators."""
    if hasattr(node, "decorator_list") and node.decorator_list:
        return node.decorator_list[0].lineno
    return node.lineno


def _count_blank_lines_before(lines: list[str], lineno: int) -> int:
    """Count consecutive blank lines before 1-based *lineno*."""
    count = 0
    for i in range(lineno - 2, -1, -1):
        if lines[i].strip() == "":
            count += 1
        else:
            break
    return count


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


def _collect_keyword_arg_equals(
    tree: ast.Module, lines: list[str]
) -> dict[int, set[int]]:
    """Return ``=`` positions that belong to keyword arguments in calls."""
    keyword_arg_equals: dict[int, set[int]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg is None:
                continue
            line_number = getattr(keyword, "lineno", None)
            if line_number is None or line_number < 1 or line_number > len(lines):
                continue
            line = lines[line_number - 1]
            start = getattr(keyword, "col_offset", None)
            if start is None or start < 0 or start >= len(line):
                continue
            equals_index = line.find("=", start)
            if equals_index == -1:
                continue
            keyword_arg_equals.setdefault(line_number, set()).add(equals_index)
    return keyword_arg_equals


def _find_equals_between(
    lines: list[str],
    start_line: int,
    start_col: int,
    end_line: int,
    end_col: int,
) -> tuple[int, int] | None:
    """Return the first ``=`` between two source positions, if any."""
    return _find_char_between(lines, start_line, start_col, end_line, end_col, "=")


def _find_char_between(
    lines: list[str],
    start_line: int,
    start_col: int,
    end_line: int,
    end_col: int,
    char: str,
) -> tuple[int, int] | None:
    """Return the first occurrence of *char* between source positions."""
    if start_line < 1 or end_line < start_line:
        return None

    for line_number in range(start_line, end_line + 1):
        if line_number < 1 or line_number > len(lines):
            return None
        line = lines[line_number - 1]
        left = start_col if line_number == start_line else 0
        right = end_col if line_number == end_line else len(line)
        left = max(0, left)
        right = min(len(line), right)
        if left > right:
            continue
        char_index = line.find(char, left, right)
        if char_index != -1:
            return line_number, char_index
    return None


def _collect_param_default_equals(
    tree: ast.Module, lines: list[str]
) -> dict[int, dict[int, bool]]:
    """Return default-parameter ``=`` positions with annotation metadata."""
    default_param_equals: dict[int, dict[int, bool]] = {}

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        arg_default_pairs: list[tuple[ast.arg, ast.expr]] = []

        positional_args = [*node.args.posonlyargs, *node.args.args]
        positional_defaults = node.args.defaults
        if positional_defaults:
            defaulted_args = positional_args[-len(positional_defaults) :]
            arg_default_pairs.extend(zip(defaulted_args, positional_defaults))

        for kw_arg, kw_default in zip(node.args.kwonlyargs, node.args.kw_defaults):
            if kw_default is None:
                continue
            arg_default_pairs.append((kw_arg, kw_default))

        for arg_node, default_node in arg_default_pairs:
            start_line = getattr(arg_node, "end_lineno", None) or getattr(
                arg_node, "lineno", None
            )
            start_col = getattr(arg_node, "end_col_offset", None)
            end_line = getattr(default_node, "lineno", None)
            end_col = getattr(default_node, "col_offset", None)
            if None in (start_line, start_col, end_line, end_col):
                continue

            eq_pos = _find_equals_between(
                lines,
                int(start_line),
                int(start_col),
                int(end_line),
                int(end_col),
            )
            if eq_pos is None:
                continue

            eq_line, eq_col = eq_pos
            default_param_equals.setdefault(eq_line, {})[eq_col] = (
                arg_node.annotation is not None
            )

    return default_param_equals


def _collect_annotation_colons(
    tree: ast.Module, lines: list[str]
) -> dict[int, set[int]]:
    """Return ``:`` positions used by variable/parameter annotations."""
    annotation_colons: dict[int, set[int]] = {}

    def _record_colon(
        start_line: int,
        start_col: int,
        end_line: int,
        end_col: int,
    ) -> None:
        colon_pos = _find_char_between(
            lines,
            start_line,
            start_col,
            end_line,
            end_col,
            ":",
        )
        if colon_pos is None:
            return
        colon_line, colon_col = colon_pos
        annotation_colons.setdefault(colon_line, set()).add(colon_col)

    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign):
            start_line = getattr(node.target, "end_lineno", None) or getattr(
                node.target, "lineno", None
            )
            start_col = getattr(node.target, "end_col_offset", None)
            end_line = getattr(node.annotation, "lineno", None)
            end_col = getattr(node.annotation, "col_offset", None)
            if None not in (start_line, start_col, end_line, end_col):
                _record_colon(
                    int(start_line),
                    int(start_col),
                    int(end_line),
                    int(end_col),
                )

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            annotated_args: list[ast.arg] = [
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            ]
            if node.args.vararg is not None:
                annotated_args.append(node.args.vararg)
            if node.args.kwarg is not None:
                annotated_args.append(node.args.kwarg)

            for arg in annotated_args:
                if arg.annotation is None:
                    continue
                start_line = getattr(arg, "lineno", None)
                start_col = getattr(arg, "col_offset", None)
                end_line = getattr(arg.annotation, "lineno", None)
                end_col = getattr(arg.annotation, "col_offset", None)
                if None in (start_line, start_col, end_line, end_col):
                    continue
                _record_colon(
                    int(start_line),
                    int(start_col),
                    int(end_line),
                    int(end_col),
                )

    return annotation_colons


# ---------------------------------------------------------------------------
# Single-pass AST visitor — consolidates all AST-based checks
# FR-ANALYSIS-001
# FR-ANALYSIS-002
# ---------------------------------------------------------------------------


class _ASTVisitor(ast.NodeVisitor):
    """Single-pass AST visitor collecting findings across all check categories."""

    def __init__(self, tree: ast.Module) -> None:
        self._tree = tree
        self.findings: list[Finding] = []
        self._flagged_names: set[str] = set()

    def run(self) -> list[Finding]:
        """Walk the tree once and return all collected findings."""
        self._check_import_ordering()
        self._check_module_level_constants()
        self._check_module_dunder_placement()
        self.visit(self._tree)
        return self.findings

    # -- Top-level iteration checks (need ordered tree.body) ----------------

    def _check_import_ordering(self) -> None:
        """Flag stdlib/third-party/local imports that are not grouped."""
        _STDLIB = sys.stdlib_module_names

        def _import_group(top_level: str, level: int = 0) -> int:
            if level > 0:
                return 2
            if top_level in _STDLIB:
                return 0
            if top_level in _LOCAL_IMPORT_ROOTS:
                return 2
            return 1

        imports: list[tuple[int, str, int]] = []
        for node in self._tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    group = _import_group(top)
                    imports.append((node.lineno, alias.name, group))
            elif isinstance(node, ast.ImportFrom):
                top = (node.module or "").split(".")[0]
                group = _import_group(top, node.level or 0)
                imports.append((node.lineno, node.module or "", group))

        highest_group = -1
        for lineno, name, group in imports:
            if group < highest_group:
                labels = {0: "stdlib", 1: "third-party", 2: "local"}
                self.findings.append(
                    Finding(
                        issue_type="import_ordering",
                        line_number=lineno,
                        severity="Low",
                        message=(
                            f"Import '{name}' ({labels[group]}) appears "
                            f"after a {labels[highest_group]} import. "
                            f"Group imports: stdlib, then third-party, "
                            f"then local."
                        ),
                    )
                )
            else:
                highest_group = max(highest_group, group)

    def _check_module_level_constants(self) -> None:
        """Flag module-level constants not using UPPER_SNAKE_CASE."""
        for stmt in self._tree.body:
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
                if _is_camel_case(name):
                    continue
                if not _is_snake_case(name) and not _is_upper_snake_case(name):
                    self.findings.append(
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

    def _check_module_dunder_placement(self) -> None:
        """Flag __all__, __author__, etc. that appear after imports."""
        seen_import = False
        for stmt in self._tree.body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                # Allow __future__ imports before dunders.
                if isinstance(stmt, ast.ImportFrom) and stmt.module == "__future__":
                    continue
                seen_import = True
                continue
            if not seen_import:
                continue
            # Check for dunder assignments after imports.
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id in _MODULE_DUNDERS:
                        self.findings.append(
                            Finding(
                                issue_type="module_dunder_placement",
                                line_number=stmt.lineno,
                                severity="Low",
                                message=(
                                    f"Module dunder '{target.id}' should "
                                    f"appear before imports (after the "
                                    f"module docstring)."
                                ),
                            )
                        )

    # -- visit_* methods (type-dispatched, single pass) ---------------------

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Handle FunctionDef checks."""
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Handle AsyncFunctionDef checks."""
        self._check_function(node)
        self.generic_visit(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Consolidated checks for function/async function definitions."""
        # missing_docstrings (function)
        if node.name not in _DUNDER_METHODS:
            if ast.get_docstring(node) is None:
                self.findings.append(
                    Finding(
                        issue_type="missing_docstring",
                        line_number=node.lineno,
                        severity="Low",
                        message=f"Function '{node.name}' is missing a docstring.",
                    )
                )

        # naming_conventions (function name camelCase)
        if not node.name.startswith("__") and _is_camel_case(node.name):
            self.findings.append(
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

        # invalid_dunder (magic method naming)
        if (
            node.name.startswith("__")
            and node.name.endswith("__")
            and len(node.name) > 4
            and node.name not in _RECOGNIZED_DUNDERS
        ):
            self.findings.append(
                Finding(
                    issue_type="invalid_dunder",
                    line_number=node.lineno,
                    severity="Med",
                    message=(
                        f"'{node.name}' is not a recognised Python "
                        f"dunder method. Use a standard name or "
                        f"remove the double underscores."
                    ),
                )
            )

        # return_consistency + implicit_return_none
        returns = _collect_returns(node)
        if returns:
            has_value = any(r.value is not None for r in returns)
            has_bare = any(r.value is None for r in returns)
            if has_value and has_bare:
                self.findings.append(
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
                # implicit_return_none: flag each bare return
                for r in returns:
                    if r.value is None:
                        self.findings.append(
                            Finding(
                                issue_type="implicit_return_none",
                                line_number=r.lineno,
                                severity="Low",
                                message=(
                                    "Use explicit 'return None' instead "
                                    "of bare 'return' when the function "
                                    "has other return values."
                                ),
                            )
                        )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Handle ClassDef checks."""
        # missing_docstrings (class)
        if ast.get_docstring(node) is None:
            self.findings.append(
                Finding(
                    issue_type="missing_docstring",
                    line_number=node.lineno,
                    severity="Low",
                    message=f"Class '{node.name}' is missing a docstring.",
                )
            )

        # naming_conventions (class PascalCase)
        if not _is_pascal_case(node.name):
            self.findings.append(
                Finding(
                    issue_type="naming_convention",
                    line_number=node.lineno,
                    severity="Low",
                    message=(
                        f"Class '{node.name}' should use " f"PascalCase (CapWords)."
                    ),
                )
            )

        # exception_inheritance (BaseException)
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "BaseException":
                self.findings.append(
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

        # exception_naming — exception classes should end with "Error"
        _exception_bases = {"Exception", "BaseException"}
        for base in node.bases:
            base_name = None
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = base.attr
            if base_name and (
                base_name in _exception_bases or base_name.endswith("Error")
            ):
                if not node.name.endswith("Error"):
                    self.findings.append(
                        Finding(
                            issue_type="exception_naming",
                            line_number=node.lineno,
                            severity="Low",
                            message=(
                                f"Exception class '{node.name}' should "
                                f"end with 'Error' (e.g., "
                                f"'{node.name}Error')."
                            ),
                        )
                    )
                break

        # self_cls (iterate methods in class body)
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
                    self.findings.append(
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
                    self.findings.append(
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

        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        """Handle Compare: none, boolean, type, empty_sequence, string_slicing."""
        all_values = [node.left] + node.comparators
        for i, op in enumerate(node.ops):
            left = all_values[i]
            right = all_values[i + 1]

            # none_comparison
            if isinstance(op, (ast.Eq, ast.NotEq)):
                if _is_none_const(left) or _is_none_const(right):
                    self.findings.append(
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

            # boolean_comparison (== True / != True / == False / != False)
            if isinstance(op, (ast.Eq, ast.NotEq)):
                if _is_bool_const(left) or _is_bool_const(right):
                    self.findings.append(
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

            # is_true_false (is True / is not True / is False / is not False)
            if isinstance(op, (ast.Is, ast.IsNot)):
                if _is_bool_const(left) or _is_bool_const(right):
                    self.findings.append(
                        Finding(
                            issue_type="is_true_false",
                            line_number=node.lineno,
                            severity="Low",
                            message=(
                                "Don't use 'is True' or 'is False'. "
                                "Test truthiness directly."
                            ),
                        )
                    )
                    break

            # type_comparison
            if isinstance(op, (ast.Is, ast.IsNot, ast.Eq, ast.NotEq)):
                if _is_type_call(left) and _is_type_call(right):
                    self.findings.append(
                        Finding(
                            issue_type="type_comparison",
                            line_number=node.lineno,
                            severity="Med",
                            message=(
                                "Use isinstance() instead of comparing "
                                "types directly."
                            ),
                        )
                    )
                    break

            # empty_sequence
            if isinstance(op, (ast.Eq, ast.NotEq, ast.Gt, ast.Lt, ast.GtE, ast.LtE)):
                if (_is_len_call(left) and _is_zero_const(right)) or (
                    _is_zero_const(left) and _is_len_call(right)
                ):
                    self.findings.append(
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

            # string_slicing
            if isinstance(op, (ast.Eq, ast.NotEq)):
                method = None
                if _is_string_slice(left) and isinstance(right, ast.Constant):
                    if isinstance(right.value, str):
                        method = _suggest_string_method(left)
                elif _is_string_slice(right) and isinstance(left, ast.Constant):
                    if isinstance(left.value, str):
                        method = _suggest_string_method(right)
                if method:
                    self.findings.append(
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

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Handle Assign checks: lambda_assignment, naming (variable)."""
        # lambda_assignment
        if isinstance(node.value, ast.Lambda):
            self.findings.append(
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

        # naming_conventions (variable camelCase + ambiguous)
        for target in node.targets:
            if isinstance(target, ast.Name) and isinstance(target.ctx, ast.Store):
                self._check_variable_name(target)

        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Handle Name checks: ambiguous/camelCase variable names."""
        if isinstance(node.ctx, ast.Store):
            self._check_variable_name(node)
        self.generic_visit(node)

    def _check_variable_name(self, node: ast.Name) -> None:
        """Check a variable name for ambiguity or camelCase."""
        if node.id in self._flagged_names:
            return
        if node.id in _AMBIGUOUS_NAMES:
            self._flagged_names.add(node.id)
            self.findings.append(
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
            self._flagged_names.add(node.id)
            self.findings.append(
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

    def visit_Import(self, node: ast.Import) -> None:
        """Handle Import checks: import_formatting."""
        if len(node.names) > 1:
            names = ", ".join(alias.name for alias in node.names)
            self.findings.append(
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
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Handle ImportFrom checks: relative_import."""
        if node.level and node.level > 0:
            self.findings.append(
                Finding(
                    issue_type="relative_import",
                    line_number=node.lineno,
                    severity="Low",
                    message=("Use absolute imports instead of relative " "imports."),
                )
            )
        self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        """Handle UnaryOp checks: is_not_preference."""
        if (
            isinstance(node.op, ast.Not)
            and isinstance(node.operand, ast.Compare)
            and len(node.operand.ops) == 1
            and isinstance(node.operand.ops[0], ast.Is)
        ):
            self.findings.append(
                Finding(
                    issue_type="is_not_preference",
                    line_number=node.lineno,
                    severity="Low",
                    message="Use 'is not' instead of 'not ... is'.",
                )
            )
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Handle ExceptHandler checks: bare_excepts."""
        if node.type is None:
            self.findings.append(
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
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Handle Try checks: try_block_scope, context_manager_usage."""
        # try_block_scope
        if len(node.body) > _TRY_BLOCK_LIMIT:
            self.findings.append(
                Finding(
                    issue_type="try_block_scope",
                    line_number=node.lineno,
                    severity="Low",
                    message=(
                        f"Try block has {len(node.body)} statements "
                        f"(limit is {_TRY_BLOCK_LIMIT}). Narrow the "
                        f"try block to only the code that may raise."
                    ),
                )
            )

        # context_manager_usage + return_in_finally
        if node.finalbody:
            for stmt in node.finalbody:
                if (
                    isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Attribute)
                    and stmt.value.func.attr == "close"
                ):
                    self.findings.append(
                        Finding(
                            issue_type="context_manager_usage",
                            line_number=node.lineno,
                            severity="Low",
                            message=(
                                "Use a 'with' statement instead of "
                                "try/finally with .close()."
                            ),
                        )
                    )
                    break

            # return_in_finally
            for child in ast.walk(ast.Module(body=node.finalbody, type_ignores=[])):
                if isinstance(child, (ast.Return, ast.Break, ast.Continue)):
                    kind = type(child).__name__.lower()
                    self.findings.append(
                        Finding(
                            issue_type="return_in_finally",
                            line_number=child.lineno,
                            severity="High",
                            message=(
                                f"Avoid '{kind}' inside a finally block. "
                                f"It silently swallows exceptions."
                            ),
                        )
                    )

        self.generic_visit(node)


# ---------------------------------------------------------------------------
# Single-pass text checks — consolidates all line-based checks
# FR-ANALYSIS-001
# FR-ANALYSIS-002
# ---------------------------------------------------------------------------


def _run_text_checks(
    code: str,
    tree: ast.Module,
    filename: str | None = None,
    keyword_arg_equals: dict[int, set[int]] | None = None,
    param_default_equals: dict[int, dict[int, bool]] | None = None,
    annotation_colons: dict[int, set[int]] | None = None,
) -> list[Finding]:
    """Run all text-based checks in a single line iteration."""
    findings: list[Finding] = []
    lines = code.splitlines()
    keyword_arg_equals = keyword_arg_equals or {}
    param_default_equals = param_default_equals or {}
    annotation_colons = annotation_colons or {}

    # module_naming — check filename is lowercase if provided
    if filename:
        import os

        base = os.path.splitext(os.path.basename(filename))[0]
        if not re.match(r"^[a-z][a-z0-9_]*$", base):
            findings.append(
                Finding(
                    issue_type="module_naming",
                    line_number=1,
                    severity="Low",
                    message=(
                        f"Module name '{base}' should be short, "
                        f"all-lowercase with underscores."
                    ),
                )
            )

    for line_number, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        leading = line[: len(line) - len(stripped)] if stripped else ""

        # long_line
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

        # trailing_whitespace
        if line != line.rstrip():
            findings.append(
                Finding(
                    issue_type="trailing_whitespace",
                    line_number=line_number,
                    severity="Low",
                    message="Line has trailing whitespace.",
                )
            )

        # tab_indentation
        if stripped and "\t" in leading:
            findings.append(
                Finding(
                    issue_type="tab_indentation",
                    line_number=line_number,
                    severity="Med",
                    message="Use spaces for indentation, not tabs.",
                )
            )

        # inline_comment_spacing
        if stripped and not stripped.startswith("#"):
            idx = _find_comment_start(line)
            if idx is not None and idx != 0:
                before = line[:idx]
                trailing_spaces = len(before) - len(before.rstrip())
                if trailing_spaces < 2:
                    findings.append(
                        Finding(
                            issue_type="inline_comment_spacing",
                            line_number=line_number,
                            severity="Low",
                            message=(
                                "Inline comments should be separated by "
                                "at least 2 spaces from the code."
                            ),
                        )
                    )

        # comment_hash_spacing
        if stripped.startswith("#"):
            if not (line_number == 1 and stripped.startswith("#!")):
                if len(stripped) > 1 and stripped[1] != " ":
                    findings.append(
                        Finding(
                            issue_type="comment_spacing",
                            line_number=line_number,
                            severity="Low",
                            message="Add a space after '#' in comments.",
                        )
                    )
        elif stripped:
            idx = _find_comment_start(line)
            if idx is not None and idx + 1 < len(line):
                if line[idx + 1] != " ":
                    findings.append(
                        Finding(
                            issue_type="comment_spacing",
                            line_number=line_number,
                            severity="Low",
                            message="Add a space after '#' in comments.",
                        )
                    )

        # --- Get code portion (excluding comments) for whitespace checks ---
        comment_idx = _find_comment_start(line)
        code_portion = line[:comment_idx] if comment_idx is not None else line

        # semicolon_statement (E702)
        if ";" in code_portion and stripped and not stripped.startswith("#"):
            findings.append(
                Finding(
                    issue_type="semicolon_statement",
                    line_number=line_number,
                    severity="Low",
                    message=(
                        "Multiple statements on one line (semicolon). "
                        "Put each statement on its own line."
                    ),
                )
            )

        # compound_statement (E701)
        if stripped and not stripped.startswith("#"):
            m = re.match(
                r"^\s*(?:if|elif|else|for|while|with|try|except|finally)\b",
                line,
            )
            if m:
                # Find the colon that ends the clause.
                colon_match = re.search(r":\s*\S", code_portion[m.end() :])
                if colon_match:
                    findings.append(
                        Finding(
                            issue_type="compound_statement",
                            line_number=line_number,
                            severity="Low",
                            message=(
                                "Compound statement — put the body on "
                                "a separate line."
                            ),
                        )
                    )

        # bracket_whitespace (E201/E202)
        if stripped and not stripped.startswith("#"):
            opening_match = re.search(r"[\(\[\{] ", code_portion)
            if opening_match:
                findings.append(
                    Finding(
                        issue_type="bracket_whitespace",
                        line_number=line_number,
                        column_start=opening_match.start() + 2,
                        column_end=opening_match.start() + 2,
                        severity="Low",
                        message=(
                            "Whitespace after opening bracket. "
                            "Remove space inside '(', '[', or '{'."
                        ),
                    )
                )
            # Ignore leading indentation so standalone closing brackets on
            # multiline calls (e.g., "    )") are not treated as E202.
            stripped_code_portion = code_portion.lstrip()
            closing_match = re.search(r" [\)\]\}]", stripped_code_portion)
            if closing_match:
                stripped_offset = len(code_portion) - len(stripped_code_portion)
                findings.append(
                    Finding(
                        issue_type="bracket_whitespace",
                        line_number=line_number,
                        column_start=stripped_offset + closing_match.start() + 1,
                        column_end=stripped_offset + closing_match.start() + 1,
                        severity="Low",
                        message=(
                            "Whitespace before closing bracket. "
                            "Remove space inside ')', ']', or '}'."
                        ),
                    )
                )

        # whitespace_before_punctuation (E203) — space before , or ;
        if stripped and not stripped.startswith("#"):
            if re.search(r" [,;]", code_portion):
                findings.append(
                    Finding(
                        issue_type="whitespace_before_punctuation",
                        line_number=line_number,
                        severity="Low",
                        message="Whitespace before ',', or ';'.",
                    )
                )

        # whitespace_before_call (E211)
        if stripped and not stripped.startswith("#"):
            # Match identifier followed by space then ( or [, but skip
            # keywords like if/for/while/with/return/assert/etc.
            _keywords = {
                "if",
                "elif",
                "for",
                "while",
                "with",
                "return",
                "assert",
                "except",
                "raise",
                "del",
                "yield",
                "import",
                "from",
                "class",
                "def",
                "and",
                "or",
                "not",
                "in",
                "is",
                "lambda",
                "print",
            }
            for wc_match in re.finditer(r"(\w+)\s+[\(\[]", code_portion):
                name = wc_match.group(1)
                if name not in _keywords and not name[0].isupper():
                    findings.append(
                        Finding(
                            issue_type="whitespace_before_call",
                            line_number=line_number,
                            severity="Low",
                            message=(
                                f"Whitespace before '(' or '['. "
                                f"Remove space after '{name}'."
                            ),
                        )
                    )
                    break

        # whitespace_after_separator (E231)
        if stripped and not stripped.startswith("#"):
            if re.search(r"[,;][^\s\]\)\}\n]", code_portion):
                findings.append(
                    Finding(
                        issue_type="whitespace_after_separator",
                        line_number=line_number,
                        severity="Low",
                        message=("Missing whitespace after ',', or ';'."),
                    )
                )

        # operator_spacing (E225) — assignment operator '=' spacing.
        if stripped and not stripped.startswith(("#", "@")):
            # Only check lines that are not def/lambda signatures
            # (to avoid false positives on default args)
            if not re.match(r"^\s*(def |lambda )", line):
                # Match single = without spaces, excluding == != <= >= **=
                for eq_match in re.finditer(
                    r"(?<![=!<>*/+\-|&^~%:])=(?!=)", code_portion
                ):
                    if eq_match.start() in keyword_arg_equals.get(line_number, set()):
                        continue
                    pos = eq_match.start()
                    left_space = pos > 0 and code_portion[pos - 1].isspace()
                    right_space = (
                        pos + 1 < len(code_portion) and code_portion[pos + 1].isspace()
                    )
                    if not (left_space and right_space):
                        findings.append(
                            Finding(
                                issue_type="operator_spacing",
                                line_number=line_number,
                                column_start=pos + 1,
                                column_end=pos + 1,
                                severity="Low",
                                message=(
                                    "Missing whitespace around assignment "
                                    "operator '='."
                                ),
                            )
                        )
                        break

        # keyword_arg_spacing (E251) — keyword args and default params
        if stripped and not stripped.startswith("#"):
            line_has_keyword_spacing_issue = False

            for kw_pos in sorted(keyword_arg_equals.get(line_number, set())):
                left_space = kw_pos > 0 and code_portion[kw_pos - 1].isspace()
                right_space = (
                    kw_pos + 1 < len(code_portion)
                    and code_portion[kw_pos + 1].isspace()
                )
                if left_space or right_space:
                    findings.append(
                        Finding(
                            issue_type="keyword_arg_spacing",
                            line_number=line_number,
                            column_start=kw_pos + 1,
                            column_end=kw_pos + 1,
                            severity="Low",
                            message="No spaces around '=' in keyword argument.",
                        )
                    )
                    line_has_keyword_spacing_issue = True
                    break

            if not line_has_keyword_spacing_issue:
                for default_pos, is_annotated in sorted(
                    param_default_equals.get(line_number, {}).items()
                ):
                    left_space = (
                        default_pos > 0 and code_portion[default_pos - 1].isspace()
                    )
                    right_space = (
                        default_pos + 1 < len(code_portion)
                        and code_portion[default_pos + 1].isspace()
                    )

                    if is_annotated and not (left_space and right_space):
                        findings.append(
                            Finding(
                                issue_type="keyword_arg_spacing",
                                line_number=line_number,
                                column_start=default_pos + 1,
                                column_end=default_pos + 1,
                                severity="Low",
                                message=(
                                    "Use spaces around '=' in annotated "
                                    "default parameter value."
                                ),
                            )
                        )
                        break

                    if (not is_annotated) and (left_space or right_space):
                        findings.append(
                            Finding(
                                issue_type="keyword_arg_spacing",
                                line_number=line_number,
                                column_start=default_pos + 1,
                                column_end=default_pos + 1,
                                severity="Low",
                                message=(
                                    "No spaces around '=' in unannotated "
                                    "default parameter value."
                                ),
                            )
                        )
                        break

        # binary_operator_line_break (W504)
        if stripped and not stripped.startswith("#"):
            rstripped = code_portion.rstrip()
            if rstripped:
                m = re.search(
                    r"\s(and|or|\+|-|\*\*|//|\*|/|%|\||\^|&)\s*$",
                    rstripped,
                )
                if m:
                    bop = m.group(1)
                    findings.append(
                        Finding(
                            issue_type="binary_operator_line_break",
                            line_number=line_number,
                            severity="Low",
                            message=(
                                f"Line break after binary "
                                f"operator '{bop}'. Break "
                                f"before the operator instead."
                            ),
                        )
                    )

        # arrow_spacing — missing spaces around -> in function signatures
        if stripped and not stripped.startswith("#"):
            if "def " in line and "->" in code_portion:
                if re.search(r"\S->|->(?!\s)", code_portion):
                    findings.append(
                        Finding(
                            issue_type="arrow_spacing",
                            line_number=line_number,
                            severity="Low",
                            message=(
                                "Missing whitespace around '->' in "
                                "function annotation."
                            ),
                        )
                    )

        # annotation_spacing — enforce ``name: Type`` style.
        if stripped and not stripped.startswith("#"):
            for colon_pos in sorted(annotation_colons.get(line_number, set())):
                has_space_before = (
                    colon_pos > 0 and code_portion[colon_pos - 1].isspace()
                )
                has_single_space_after = (
                    colon_pos + 1 < len(code_portion)
                    and code_portion[colon_pos + 1] == " "
                )
                if has_space_before or not has_single_space_after:
                    findings.append(
                        Finding(
                            issue_type="annotation_spacing",
                            line_number=line_number,
                            column_start=colon_pos + 1,
                            column_end=colon_pos + 1,
                            severity="Low",
                            message=(
                                "Annotation spacing should be 'name: Type' "
                                "(no space before ':', one space after)."
                            ),
                        )
                    )
                    break

        # block_comment_capitalization
        if stripped.startswith("# ") and len(stripped) > 2:
            if not any(stripped.startswith(p) for p in _COMMENT_SKIP_PREFIXES):
                first_word = stripped[2:].split()[0] if stripped[2:].split() else ""
                if first_word and first_word[0].islower() and first_word[0].isalpha():
                    # Only flag if not a code identifier (heuristic: no dots/parens)
                    if "." not in first_word and "(" not in first_word:
                        findings.append(
                            Finding(
                                issue_type="block_comment_capitalization",
                                line_number=line_number,
                                severity="Low",
                                message=(
                                    "Block comment should start with a "
                                    "capitalised word."
                                ),
                            )
                        )

    # triple_quote_style (regex over full code)
    flagged_lines: set[int] = set()
    for match in re.finditer(r"'''", code):
        line_number = code[: match.start()].count("\n") + 1
        if line_number not in flagged_lines:
            flagged_lines.add(line_number)
            findings.append(
                Finding(
                    issue_type="triple_quote_style",
                    line_number=line_number,
                    severity="Low",
                    message=(
                        'Use triple double quotes (""") instead '
                        "of triple single quotes (''')."
                    ),
                )
            )

    # quote_consistency (whole-file check)
    single_count = len(re.findall(r"(?<!')(?<!\")(?<!\\)'(?!'')", code))
    double_count = len(re.findall(r'(?<!")(?<!\\)"(?!"")', code))
    total_quotes = single_count + double_count
    if total_quotes > 5:
        dominant = "double" if double_count >= single_count else "single"
        ratio = max(single_count, double_count) / total_quotes
        if ratio > 0.7:
            minority = "single" if dominant == "double" else "double"
            minority_pattern = (
                r"(?<!')(?<!\")(?<!\\)'(?!'')"
                if minority == "single"
                else r'(?<!")(?<!\\)"(?!"")'
            )
            for qm in re.finditer(minority_pattern, code):
                qline = code[: qm.start()].count("\n") + 1
                findings.append(
                    Finding(
                        issue_type="quote_consistency",
                        line_number=qline,
                        severity="Low",
                        message=(
                            f"Inconsistent quote style. File "
                            f"predominantly uses {dominant} quotes."
                        ),
                    )
                )
                break  # Only flag once

    # block_comment_indentation (needs lookahead across lines)
    for idx_bc, bc_line in enumerate(lines):
        bc_stripped = bc_line.lstrip()
        if not bc_stripped.startswith("#"):
            continue
        bc_indent = len(bc_line) - len(bc_stripped)
        # Find next non-blank, non-comment line
        for future_idx in range(idx_bc + 1, len(lines)):
            future = lines[future_idx]
            fs = future.lstrip()
            if not fs or fs.startswith("#"):
                continue
            code_indent = len(future) - len(fs)
            if bc_indent != code_indent:
                findings.append(
                    Finding(
                        issue_type="block_comment_indentation",
                        line_number=idx_bc + 1,
                        severity="Low",
                        message=(
                            "Block comment indentation does not match "
                            "the following code block."
                        ),
                    )
                )
            break

    # blank_line_spacing (needs both lines list and tree)
    findings.extend(_check_blank_line_spacing(lines, tree))

    return findings


def _check_blank_line_spacing(lines: list[str], tree: ast.Module) -> list[Finding]:
    """Verify 2 blank lines before top-level defs and 1 between methods."""
    findings: list[Finding] = []

    # Top-level defs: require 2 blank lines (skip first statement).
    for i, stmt in enumerate(tree.body):
        if i == 0:
            continue
        if not isinstance(
            stmt,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            continue
        start = _effective_start(stmt)
        blanks = _count_blank_lines_before(lines, start)
        if blanks < 2:
            findings.append(
                Finding(
                    issue_type="blank_line_spacing",
                    line_number=start,
                    severity="Low",
                    message=(
                        f"Expected 2 blank lines before top-level "
                        f"definition, found {blanks}."
                    ),
                )
            )

    # Class methods: require 1 blank line between methods.
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        methods = [
            n
            for n in node.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        for j in range(1, len(methods)):
            start = _effective_start(methods[j])
            blanks = _count_blank_lines_before(lines, start)
            if blanks < 1:
                findings.append(
                    Finding(
                        issue_type="blank_line_spacing",
                        line_number=start,
                        severity="Low",
                        message=(
                            f"Expected 1 blank line before method "
                            f"definition, found {blanks}."
                        ),
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class PythonEngine:
    """Static analysis engine for Python source code.

    FR-ANALYSIS-001
    FR-ANALYSIS-002
    """

    # FR-REPORT-001
    @staticmethod
    def compute_score(
        findings: list[Finding],
        predicted_bugs: list[PredictedBug],
    ) -> int:
        """Compute an overall quality score (0-100) from findings and predicted bugs.

        Args:
            findings: Static analysis findings with Low / Med / High severity.
            predicted_bugs: GPT-predicted bugs with low / medium / high / critical
                severity.

        Returns:
            An integer score between 0 and 100 inclusive.
        """
        penalty = 0
        for f in findings:
            penalty += _SEVERITY_PENALTIES.get(f.severity, 0)
        for b in predicted_bugs:
            # CodeBERT flagged this as a likely GPT hallucination — zero penalty.
            if getattr(b, "flagged", False):
                continue
            penalty += _SEVERITY_PENALTIES.get(b.severity, 0)
        return max(0, 100 - penalty)

    # FR-ANALYSIS-001
    # FR-ANALYSIS-002
    # NFR-RELI-001
    @staticmethod
    def run_static_analysis(
        code: str,
        filename: str | None = None,
    ) -> tuple[list[Finding], int]:
        """Run all static checks against *code* and return findings with a raw score.

        The returned score is based on static findings only.  The caller should
        invoke :meth:`compute_score` again once GPT predictions are available to
        produce the final score.

        Args:
            code: The Python source code string to analyse.
            filename: Optional filename for module-naming checks.

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
            raw_score = PythonEngine.compute_score(findings, [])
            return findings, raw_score

        # Single-pass text-based checks.
        lines = code.splitlines()
        keyword_arg_equals = _collect_keyword_arg_equals(tree, lines)
        param_default_equals = _collect_param_default_equals(tree, lines)
        annotation_colons = _collect_annotation_colons(tree, lines)
        findings.extend(
            _run_text_checks(
                code,
                tree,
                filename,
                keyword_arg_equals,
                param_default_equals,
                annotation_colons,
            )
        )

        # Single-pass AST-based checks.
        visitor = _ASTVisitor(tree)
        findings.extend(visitor.run())

        raw_score = PythonEngine.compute_score(findings, [])
        logger.debug(
            "Static analysis complete: %d findings, raw score %d",
            len(findings),
            raw_score,
        )
        return findings, raw_score

    @staticmethod
    def supported_checks() -> list[str]:
        """Return the list of all issue_type strings this engine can produce."""
        return [
            # Supported static analysis checks.
            "syntax_error",
            "long_line",
            "trailing_whitespace",
            "tab_indentation",
            "inline_comment_spacing",
            "comment_spacing",
            "triple_quote_style",
            "blank_line_spacing",
            "missing_docstring",
            "bare_except",
            "naming_convention",
            "ambiguous_name",
            "self_cls_naming",
            "none_comparison",
            "boolean_comparison",
            "type_comparison",
            "empty_sequence_check",
            "lambda_assignment",
            "import_formatting",
            "is_not_preference",
            "return_consistency",
            "exception_inheritance",
            "string_slicing",
            "import_ordering",
            "try_block_scope",
            "context_manager_usage",
            "is_true_false",
            "exception_naming",
            "invalid_dunder",
            "return_in_finally",
            "implicit_return_none",
            "module_dunder_placement",
            "relative_import",
            "bracket_whitespace",
            "whitespace_before_punctuation",
            "whitespace_before_call",
            "operator_spacing",
            "whitespace_after_separator",
            "keyword_arg_spacing",
            "semicolon_statement",
            "compound_statement",
            "block_comment_capitalization",
            "block_comment_indentation",
            "binary_operator_line_break",
            "annotation_spacing",
            "arrow_spacing",
            "quote_consistency",
            "module_naming",
        ]
