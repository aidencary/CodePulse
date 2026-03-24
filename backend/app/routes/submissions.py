"""Submissions CRUD endpoints — list, rename, delete, and pin submissions."""

import logging
from datetime import datetime, timezone

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
        .select(
            "submission_id, name, created_at, pinned_at,"
            " analysis_reports(overall_score)"
        )
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
                pinned_at=row.get("pinned_at"),
            )
        )

    # Sort: pinned first (by pinned_at desc), then unpinned (by created_at desc).
    items.sort(
        key=lambda s: (s.pinned_at is not None, s.pinned_at or ""),
        reverse=True,
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


@router.patch("/{submission_id}/pin")
async def toggle_pin(
    submission_id: str,
    user_id: str = Depends(get_current_user),
):
    """Toggle the pinned status of a submission."""
    sb = get_supabase_client()

    # Verify ownership.
    existing = (
        sb.table("submissions")
        .select("user_id, pinned_at")
        .eq("submission_id", submission_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )
    if existing.data[0]["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your submission",
        )

    # Toggle: if currently pinned, unpin; otherwise pin.
    currently_pinned = existing.data[0].get("pinned_at")
    new_value = None if currently_pinned else datetime.now(timezone.utc).isoformat()

    sb.table("submissions").update({"pinned_at": new_value}).eq(
        "submission_id", submission_id
    ).execute()

    return {"pinned": new_value is not None, "pinned_at": new_value}
