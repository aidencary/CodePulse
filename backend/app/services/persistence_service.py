"""Persistence service — writes analysis results to Supabase."""

import logging

from app.database import get_supabase_client
from app.models.analysis import Finding, PredictedBug

logger = logging.getLogger(__name__)


class PersistenceError(Exception):
    """Raised when a Supabase write fails during analysis persistence."""


# FR-HIST-001
# NFR-SEC-001
async def persist_analysis(
    user_id: str,
    code: str,
    overall_score: int,
    summary: str,
    findings: list[Finding],
    predicted_bugs: list[PredictedBug],
    name: str | None = None,
) -> tuple[str, str | None]:
    """Persist a complete analysis result to Supabase and return the submission ID.

    Writes rows in dependency order:
    1. ``submissions``
    2. ``analysis_reports``
    3. ``findings``
    4. ``predicted_bugs``

    The ``actionable_fixes`` table is intentionally skipped — the static analyzer
    does not currently produce ``original_snippet`` values.

    Args:
        user_id: Authenticated user's UUID.
        code: Raw code string submitted by the user.
        overall_score: Final quality score (0–100).
        summary: Human-readable one-line summary.
        findings: Static analysis findings.
        predicted_bugs: GPT-predicted bugs.

    Returns:
        A tuple of (``submission_id``, ``name``) for the newly created submission.

    Raises:
        PersistenceError: If any database write fails.
    """
    try:
        client = get_supabase_client()

        # 1. Insert submission.
        row = {"user_id": user_id, "code": code}
        if name is not None:
            row["name"] = name
        sub_result = client.table("submissions").insert(row).execute()
        submission_id: str = sub_result.data[0]["submission_id"]
        persisted_name: str | None = sub_result.data[0].get("name")

        # 2. Insert analysis report.
        report_result = (
            client.table("analysis_reports")
            .insert(
                {
                    "submission_id": submission_id,
                    "overall_score": overall_score,
                    "summary": summary,
                }
            )
            .execute()
        )
        report_id: str = report_result.data[0]["report_id"]

        # 3. Insert findings (bulk).
        if findings:
            findings_rows = [
                {
                    "report_id": report_id,
                    "issue_type": f.issue_type,
                    "line_number": f.line_number,
                    "line_severity": f.severity,  # DB column is line_severity
                    "message": f.message,
                }
                for f in findings
            ]
            client.table("findings").insert(findings_rows).execute()

        # 4. Insert predicted bugs (bulk).
        if predicted_bugs:
            bugs_rows = [
                {
                    "report_id": report_id,
                    "line_number": b.line_number,
                    "bug_type": b.bug_type,
                    "severity": b.severity,
                    "description": b.description,
                    "suggested_fix": b.suggested_fix,
                }
                for b in predicted_bugs
            ]
            client.table("predicted_bugs").insert(bugs_rows).execute()

        logger.info(
            "Persisted analysis for user %s: submission=%s, report=%s, "
            "%d findings, %d predicted bugs.",
            user_id,
            submission_id,
            report_id,
            len(findings),
            len(predicted_bugs),
        )
        return submission_id, persisted_name

    except Exception as exc:
        logger.error("Failed to persist analysis for user %s: %s", user_id, exc)
        raise PersistenceError(str(exc)) from exc


# FR-ANALYSIS-005
# NFR-SEC-001
async def reanalyze_submission(
    submission_id: str,
    user_id: str,
    code: str,
    overall_score: int,
    summary: str,
    findings: list[Finding],
    predicted_bugs: list[PredictedBug],
) -> tuple[str, str | None]:
    """Re-run analysis on an existing submission.

    Deletes the old analysis data (cascade handles findings, bugs, fixes),
    updates the code column, then writes fresh analysis results.
    Preserves the original submission name.

    Args:
        submission_id: UUID of the existing submission.
        user_id: Authenticated user's UUID (for ownership check).
        code: Updated code string.
        overall_score: New quality score (0-100).
        summary: New human-readable summary.
        findings: New static analysis findings.
        predicted_bugs: New GPT-predicted bugs.

    Returns:
        A tuple of (``submission_id``, ``name``).

    Raises:
        PersistenceError: If any database write fails.
    """
    try:
        client = get_supabase_client()

        # 1. Verify ownership and get current name.
        existing = (
            client.table("submissions")
            .select("user_id, name")
            .eq("submission_id", submission_id)
            .execute()
        )
        if not existing.data:
            raise PersistenceError("Submission not found")
        if existing.data[0]["user_id"] != user_id:
            raise PersistenceError("Not your submission")

        persisted_name = existing.data[0].get("name")

        # 2. Delete old analysis report (cascade deletes findings,
        #    actionable_fixes, and predicted_bugs).
        client.table("analysis_reports").delete().eq(
            "submission_id", submission_id
        ).execute()

        # 3. Update the code column.
        client.table("submissions").update({"code": code}).eq(
            "submission_id", submission_id
        ).execute()

        # 4. Insert new analysis report.
        report_result = (
            client.table("analysis_reports")
            .insert(
                {
                    "submission_id": submission_id,
                    "overall_score": overall_score,
                    "summary": summary,
                }
            )
            .execute()
        )
        report_id: str = report_result.data[0]["report_id"]

        # 5. Insert findings (bulk).
        if findings:
            findings_rows = [
                {
                    "report_id": report_id,
                    "issue_type": f.issue_type,
                    "line_number": f.line_number,
                    "line_severity": f.severity,
                    "message": f.message,
                }
                for f in findings
            ]
            client.table("findings").insert(findings_rows).execute()

        # 6. Insert predicted bugs (bulk).
        if predicted_bugs:
            bugs_rows = [
                {
                    "report_id": report_id,
                    "line_number": b.line_number,
                    "bug_type": b.bug_type,
                    "severity": b.severity,
                    "description": b.description,
                    "suggested_fix": b.suggested_fix,
                }
                for b in predicted_bugs
            ]
            client.table("predicted_bugs").insert(bugs_rows).execute()

        logger.info(
            "Reanalyzed submission %s for user %s: report=%s, "
            "%d findings, %d predicted bugs.",
            submission_id,
            user_id,
            report_id,
            len(findings),
            len(predicted_bugs),
        )
        return submission_id, persisted_name

    except PersistenceError:
        raise
    except Exception as exc:
        logger.error(
            "Failed to reanalyze submission %s: %s",
            submission_id,
            exc,
        )
        raise PersistenceError(str(exc)) from exc
