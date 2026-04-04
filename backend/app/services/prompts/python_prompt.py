"""GPT prompt templates for Python code analysis."""

from app.models.analysis import Finding

MAX_BUGS_RETURNED = 10


def build_system_prompt(findings: list[Finding], language: str) -> str:
    """Build the system prompt, summarising any static findings to avoid duplication."""
    findings_summary = (
        "\n".join(
            f"  - Line {f.line_number}: [{f.severity}] {f.issue_type} — {f.message}"
            for f in findings
        )
        if findings
        else "  (none)"
    )

    return f"""You are an expert code quality analyst specialising in bug detection.
Analyse the provided {language} code for bugs, logic errors, security vulnerabilities,
and potential runtime failures that are NOT already listed below.

Static analysis has already flagged:
{findings_summary}

Do NOT repeat issues from the list above.

Respond ONLY with valid JSON matching this exact schema — no markdown, no prose:
{{
  "predicted_bugs": [
    {{
      "line_number": <integer or null>,
      "bug_type": <string — e.g. "null_dereference", "sql_injection", "off_by_one">,
      "severity": <"low" | "medium" | "high" | "critical">,
      "description": <string — one sentence explaining the bug>,
      "suggested_fix": <string — concrete code change or approach to fix it>
    }}
  ]
}}

Return at most {MAX_BUGS_RETURNED} bugs. Return an empty array if no bugs are found."""


def build_user_message(code: str, language: str) -> str:
    """Wrap code in a prompt with explicit line numbers for accurate GPT references."""
    numbered = "\n".join(f"{i + 1}: {line}" for i, line in enumerate(code.splitlines()))
    return f"Analyse the following {language} code:\n\n```\n{numbered}\n```"
