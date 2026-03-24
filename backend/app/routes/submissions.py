"""Submissions CRUD endpoints — list, rename, and delete submissions."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_supabase_client
from app.dependencies import get_current_user
from app.models.analysis import SubmissionListItem, SubmissionRenameRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.get("", response_model=list[SubmissionListItem])
async def list_submissions(user_id: str = Depends(get_current_user)):
    """Return all submissions for the authenticated user with optional score."""
    sb = get_supabase_client()

    result = (
        sb.table("submissions")
        .select("submission_id, name, created_at, analysis_reports(overall_score)")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    items = []
    for row in result.data:
        report = row.get("analysis_reports")
        # Supabase returns a single object (1:1) or a list — normalise.
        if isinstance(report, list):
            score = report[0]["overall_score"] if report else None
        elif isinstance(report, dict):
            score = report.get("overall_score")
        else:
            score = None

        items.append(
            SubmissionListItem(
                submission_id=row["submission_id"],
                name=row.get("name"),
                created_at=row["created_at"],
                overall_score=score,
            )
        )

    return items


@router.patch("/{submission_id}", response_model=SubmissionListItem)
async def rename_submission(
    submission_id: str,
    body: SubmissionRenameRequest,
    user_id: str = Depends(get_current_user),
):
    """Rename a submission. The caller must own the submission."""
    sb = get_supabase_client()

    # Verify ownership
    existing = (
        sb.table("submissions")
        .select("user_id")
        .eq("submission_id", submission_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )
    if existing.data[0]["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your submission"
        )

    # Update the name
    result = (
        sb.table("submissions")
        .update({"name": body.name})
        .eq("submission_id", submission_id)
        .execute()
    )
    row = result.data[0]

    # Fetch score
    report = (
        sb.table("analysis_reports")
        .select("overall_score")
        .eq("submission_id", submission_id)
        .execute()
    )
    score = report.data[0]["overall_score"] if report.data else None

    return SubmissionListItem(
        submission_id=row["submission_id"],
        name=row.get("name"),
        created_at=row["created_at"],
        overall_score=score,
    )


@router.delete("/{submission_id}", status_code=status.HTTP_200_OK)
async def delete_submission(
    submission_id: str,
    user_id: str = Depends(get_current_user),
):
    """Delete a submission owned by the caller.

    Cascade handles related rows.
    """
    sb = get_supabase_client()

    # Verify ownership
    existing = (
        sb.table("submissions")
        .select("user_id")
        .eq("submission_id", submission_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )
    if existing.data[0]["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your submission"
        )

    sb.table("submissions").delete().eq("submission_id", submission_id).execute()

    return {"detail": "Submission deleted"}
