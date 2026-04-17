"""Account CRUD endpoints for profile management."""

import asyncio
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.config import get_settings
from app.database import get_supabase_client
from app.dependencies import get_current_user
from app.models.account import (
    AvatarUploadResponse,
    ChangePasswordRequest,
    DataExportResponse,
    InviteUserRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["account"])

ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 MB


# ------------------------------------------------------------------
# GET /account/profile
# ------------------------------------------------------------------
# FR-ACCT-001
@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user_id: str = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    sb = get_supabase_client()

    # Fetch profile row and auth email concurrently (independent calls).
    result, auth_user = await asyncio.gather(
        asyncio.to_thread(sb.table("profiles").select("*").eq("id", user_id).execute),
        asyncio.to_thread(sb.auth.admin.get_user_by_id, user_id),
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    profile = result.data[0]
    email = auth_user.user.email if auth_user and auth_user.user else ""

    return ProfileResponse(
        id=profile["id"],
        email=email,
        username=profile["username"],
        role=profile.get("role", "developer"),
        profile_picture=profile.get("profile_picture"),
        created_at=profile["created_at"],
    )


# ------------------------------------------------------------------
# PATCH /account/profile
# ------------------------------------------------------------------
# FR-ACCT-001
@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user),
):
    """Update the authenticated user's username and/or profile picture URL."""
    sb = get_supabase_client()

    updates: dict = {}
    metadata_updates: dict = {}

    if body.username is not None:
        # Check uniqueness
        existing = (
            sb.table("profiles")
            .select("id")
            .eq("username", body.username)
            .neq("id", user_id)
            .execute()
        )
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        updates["username"] = body.username
        metadata_updates["username"] = body.username

    if body.profile_picture is not None:
        updates["profile_picture"] = body.profile_picture
        metadata_updates["avatar_url"] = body.profile_picture

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields to update",
        )

    # Update profiles table
    sb.table("profiles").update(updates).eq("id", user_id).execute()

    # Keep auth user_metadata in sync
    if metadata_updates:
        sb.auth.admin.update_user_by_id(user_id, {"user_metadata": metadata_updates})

    # Return the updated profile
    return await get_profile(user_id)


# ------------------------------------------------------------------
# POST /account/avatar
# ------------------------------------------------------------------
# FR-ACCT-002
@router.post("/avatar", response_model=AvatarUploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    """Upload a profile picture to Supabase Storage."""
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Unsupported file type: {file.content_type}. "
                "Allowed: png, jpeg, webp"
            ),
        )

    contents = await file.read()

    if len(contents) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 2 MB",
        )

    sb = get_supabase_client()

    # Build storage path: avatars/{user_id}/avatar.{ext}
    ext = (file.filename or "avatar.png").rsplit(".", 1)[-1] if file.filename else "png"
    storage_path = f"{user_id}/avatar.{ext}"

    # Upload (upsert to overwrite previous avatar)
    sb.storage.from_("avatars").upload(
        storage_path,
        contents,
        file_options={"content-type": file.content_type, "upsert": "true"},
    )

    # Build the public URL
    public_url = sb.storage.from_("avatars").get_public_url(storage_path)

    # Update profile and auth metadata
    sb.table("profiles").update({"profile_picture": public_url}).eq(
        "id", user_id
    ).execute()
    sb.auth.admin.update_user_by_id(
        user_id, {"user_metadata": {"avatar_url": public_url}}
    )

    return AvatarUploadResponse(profile_picture=public_url)


# ------------------------------------------------------------------
# POST /account/change-password
# ------------------------------------------------------------------
# FR-ACCT-003
@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    body: ChangePasswordRequest,
    user_id: str = Depends(get_current_user),
):
    """Change the authenticated user's password."""
    sb = get_supabase_client()

    # Get user email for verification
    auth_user = sb.auth.admin.get_user_by_id(user_id)
    if not auth_user or not auth_user.user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    email = auth_user.user.email

    # Verify current password by attempting a sign-in
    try:
        sb.auth.sign_in_with_password(
            {"email": email, "password": body.current_password}
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Update to new password
    sb.auth.admin.update_user_by_id(user_id, {"password": body.new_password})

    return {"detail": "Password changed successfully"}


# ------------------------------------------------------------------
# POST /account/invite
# ------------------------------------------------------------------
# FR-ACCT-005
# FR-DASH-005
@router.post("/invite", status_code=status.HTTP_200_OK)
async def invite_user(
    body: InviteUserRequest,
    user_id: str = Depends(get_current_user),
):
    """Send a Supabase invite email to the given address."""
    sb = get_supabase_client()
    settings = get_settings()

    try:
        sb.auth.admin.invite_user_by_email(
            body.email,
            options={"redirect_to": settings.site_url},
        )
    except Exception as exc:
        logger.error("Failed to invite %s: %s", body.email, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return {"detail": f"Invite sent to {body.email}"}


# ------------------------------------------------------------------
# GET /account/export
# ------------------------------------------------------------------
# FR-ACCT-006
@router.get("/export", response_model=DataExportResponse)
async def export_data(user_id: str = Depends(get_current_user)):
    """Return all user data (profile + submissions + reports) for GDPR/CCPA export."""
    sb = get_supabase_client()

    # Fetch profile
    profile_result = sb.table("profiles").select("*").eq("id", user_id).execute()
    if not profile_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )
    profile = profile_result.data[0]

    # Fetch email from auth
    auth_user = sb.auth.admin.get_user_by_id(user_id)
    email = auth_user.user.email if auth_user and auth_user.user else ""

    # Fetch submissions with their analysis reports
    submissions_result = (
        sb.table("submissions")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    submissions = submissions_result.data or []

    # For each submission, fetch its analysis report and related data
    enriched_submissions = []
    for sub in submissions:
        entry = dict(sub)
        report_result = (
            sb.table("analysis_reports")
            .select("*")
            .eq("submission_id", sub["submission_id"])
            .execute()
        )
        if report_result.data:
            report = report_result.data[0]
            entry["report"] = report

            # Fetch findings
            findings_result = (
                sb.table("findings")
                .select("*")
                .eq("report_id", report["report_id"])
                .execute()
            )
            entry["report"]["findings"] = findings_result.data or []

            # Fetch predicted bugs
            bugs_result = (
                sb.table("predicted_bugs")
                .select("*")
                .eq("report_id", report["report_id"])
                .execute()
            )
            entry["report"]["predicted_bugs"] = bugs_result.data or []
        else:
            entry["report"] = None

        enriched_submissions.append(entry)

    return DataExportResponse(
        profile=ProfileResponse(
            id=profile["id"],
            email=email,
            username=profile["username"],
            role=profile.get("role", "developer"),
            profile_picture=profile.get("profile_picture"),
            created_at=profile["created_at"],
        ),
        submissions=enriched_submissions,
    )


# ------------------------------------------------------------------
# DELETE /account
# ------------------------------------------------------------------
# FR-ACCT-004
@router.delete("", status_code=status.HTTP_200_OK)
async def delete_account(user_id: str = Depends(get_current_user)):
    """Delete the authenticated user's account. DB cascades handle related data."""
    sb = get_supabase_client()

    try:
        sb.auth.admin.delete_user(user_id)
    except Exception as exc:
        logger.error("Failed to delete user %s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account",
        )

    return {"detail": "Account deleted successfully"}
