"""Integration tests for account CRUD endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from jose import jwt

from app.config import Settings, get_settings
from app.main import app

_TEST_JWT_SECRET = "test-secret-key-for-unit-testing-only"

_USER_ID = "00000000-0000-0000-0000-000000000001"

_PROFILE_ROW = {
    "id": _USER_ID,
    "username": "testuser",
    "role": "developer",
    "profile_picture": None,
    "created_at": "2025-01-01T00:00:00+00:00",
}


def _override_settings() -> Settings:
    """Return a Settings instance wired to test values (no .env required)."""
    return Settings.model_construct(
        supabase_url="https://test.supabase.co",
        supabase_anon_key="test-anon-key",
        supabase_service_role_key="test-service-role-key",
        supabase_jwt_secret=_TEST_JWT_SECRET,
        openai_api_key="test-openai-key",
        gpt_model="gpt-4o",
    )


app.dependency_overrides[get_settings] = _override_settings

client = TestClient(app)


def _make_token(user_id: str = _USER_ID) -> str:
    """Sign a JWT with the claims required by get_current_user."""
    return jwt.encode(
        {
            "sub": user_id,
            "aud": "authenticated",
            "iss": "https://test.supabase.co/auth/v1",
        },
        _TEST_JWT_SECRET,
        algorithm="HS256",
    )


def _make_headers(user_id: str = _USER_ID) -> dict[str, str]:
    return {"Authorization": f"Bearer {_make_token(user_id)}"}


_SUBMISSION_ROW = {
    "submission_id": "sub-001",
    "user_id": _USER_ID,
    "name": "test.py",
    "code": "print('hello')",
    "pinned_at": None,
    "created_at": "2025-02-01T00:00:00+00:00",
}

_REPORT_ROW = {
    "report_id": "rpt-001",
    "submission_id": "sub-001",
    "overall_score": 85,
    "summary": "Good code quality",
}


def _make_mock_supabase(
    profile_row: dict | None = None,
    existing_username_data: list | None = None,
):
    """Build a MagicMock that mimics a Supabase Python client with chaining."""
    sb = MagicMock()

    # Table query builder — supports method chaining
    builder = MagicMock()
    builder.select.return_value = builder
    builder.eq.return_value = builder
    builder.neq.return_value = builder
    builder.update.return_value = builder
    builder.delete.return_value = builder
    builder.insert.return_value = builder
    builder.order.return_value = builder

    # Default execute returns a profile row
    row = profile_row if profile_row is not None else dict(_PROFILE_ROW)
    builder.execute.return_value = MagicMock(data=[row])

    sb.table.return_value = builder

    # Auth admin helpers
    sb.auth.admin.get_user_by_id.return_value = MagicMock(
        user=MagicMock(email="test@example.com")
    )
    sb.auth.admin.update_user_by_id.return_value = None
    sb.auth.admin.delete_user.return_value = None

    # Storage helpers
    storage_bucket = MagicMock()
    storage_bucket.upload.return_value = None
    storage_bucket.get_public_url.return_value = (
        "https://cdn.test.co/avatars/avatar.png"
    )
    sb.storage.from_.return_value = storage_bucket

    return sb, builder


# ------------------------------------------------------------------
# GET /api/v1/account/profile
# ------------------------------------------------------------------


# TC-ACCT-001
def test_get_profile_success() -> None:
    """GET /profile returns 200 with correct response shape."""
    sb, _ = _make_mock_supabase()
    with patch("app.routes.account.get_supabase_client", return_value=sb):
        resp = client.get("/api/v1/account/profile", headers=_make_headers())

    assert resp.status_code == 200
    body = resp.json()
    for key in ("id", "email", "username", "role", "profile_picture", "created_at"):
        assert key in body, f"Missing key: {key}"
    assert body["id"] == _USER_ID
    assert body["email"] == "test@example.com"
    assert body["username"] == "testuser"


# TC-ACCT-002
def test_get_profile_no_auth() -> None:
    """GET /profile without Authorization header returns 422."""
    resp = client.get("/api/v1/account/profile")
    assert resp.status_code == 422


# ------------------------------------------------------------------
# PATCH /api/v1/account/profile
# ------------------------------------------------------------------


# TC-ACCT-003
def test_update_profile_username() -> None:
    """PATCH /profile updates the username and returns 200."""
    sb, builder = _make_mock_supabase()
    updated_row = dict(_PROFILE_ROW, username="newname")

    call_count = {"n": 0}

    def _execute_side_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # Uniqueness check — no conflict
            return MagicMock(data=[])
        # Subsequent calls (update, re-fetch) return updated row
        return MagicMock(data=[updated_row])

    builder.execute.side_effect = _execute_side_effect

    with patch("app.routes.account.get_supabase_client", return_value=sb):
        resp = client.patch(
            "/api/v1/account/profile",
            json={"username": "newname"},
            headers=_make_headers(),
        )

    assert resp.status_code == 200
    assert resp.json()["username"] == "newname"


# TC-ACCT-004
def test_update_profile_duplicate_username() -> None:
    """PATCH /profile with a taken username returns 409."""
    sb, builder = _make_mock_supabase()

    # We need the uniqueness check to find a conflict.
    # The route calls: select("id").eq("username", ...).neq("id", ...).execute()
    # We make that return a conflicting row.
    call_count = {"n": 0}
    original_execute = builder.execute

    def _execute_side_effect(*args, **kwargs):
        call_count["n"] += 1
        # First execute is the uniqueness check
        if call_count["n"] == 1:
            return MagicMock(data=[{"id": "other-user"}])
        return original_execute(*args, **kwargs)

    builder.execute.side_effect = _execute_side_effect

    with patch("app.routes.account.get_supabase_client", return_value=sb):
        resp = client.patch(
            "/api/v1/account/profile",
            json={"username": "takenname"},
            headers=_make_headers(),
        )

    assert resp.status_code == 409
    assert "already taken" in resp.json()["detail"].lower()


# TC-ACCT-005
def test_update_profile_invalid_username_chars() -> None:
    """PATCH /profile with invalid characters returns 422."""
    sb, _ = _make_mock_supabase()
    with patch("app.routes.account.get_supabase_client", return_value=sb):
        resp = client.patch(
            "/api/v1/account/profile",
            json={"username": "bad user!"},
            headers=_make_headers(),
        )

    assert resp.status_code == 422


# TC-ACCT-006
def test_update_profile_no_fields() -> None:
    """PATCH /profile with empty body returns 422."""
    sb, _ = _make_mock_supabase()
    with patch("app.routes.account.get_supabase_client", return_value=sb):
        resp = client.patch(
            "/api/v1/account/profile",
            json={},
            headers=_make_headers(),
        )

    assert resp.status_code == 422


# ------------------------------------------------------------------
# POST /api/v1/account/change-password
# ------------------------------------------------------------------


# TC-ACCT-007
def test_change_password_success() -> None:
    """POST /change-password returns 200 on valid credentials."""
    sb, _ = _make_mock_supabase()
    sb.auth.sign_in_with_password.return_value = MagicMock()

    with patch("app.routes.account.get_supabase_client", return_value=sb):
        resp = client.post(
            "/api/v1/account/change-password",
            json={"current_password": "OldPass123", "new_password": "NewPass1234"},
            headers=_make_headers(),
        )

    assert resp.status_code == 200
    assert "successfully" in resp.json()["detail"].lower()


# TC-ACCT-008
def test_change_password_wrong_current() -> None:
    """POST /change-password with wrong current password returns 401."""
    sb, _ = _make_mock_supabase()
    sb.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")

    with patch("app.routes.account.get_supabase_client", return_value=sb):
        resp = client.post(
            "/api/v1/account/change-password",
            json={"current_password": "WrongPass", "new_password": "NewPass1234"},
            headers=_make_headers(),
        )

    assert resp.status_code == 401
    assert "incorrect" in resp.json()["detail"].lower()


# TC-ACCT-009
def test_change_password_too_short() -> None:
    """POST /change-password with new password < 8 chars returns 422."""
    resp = client.post(
        "/api/v1/account/change-password",
        json={"current_password": "OldPass123", "new_password": "short"},
        headers=_make_headers(),
    )
    assert resp.status_code == 422


# ------------------------------------------------------------------
# POST /api/v1/account/avatar
# ------------------------------------------------------------------


# TC-ACCT-010
def test_upload_avatar_success() -> None:
    """POST /avatar with a valid image returns 200 with profile_picture URL."""
    sb, _ = _make_mock_supabase()

    with patch("app.routes.account.get_supabase_client", return_value=sb):
        resp = client.post(
            "/api/v1/account/avatar",
            files={"file": ("avatar.png", b"fake-png-data", "image/png")},
            headers=_make_headers(),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "profile_picture" in body
    assert body["profile_picture"].startswith("https://")


# TC-ACCT-011
def test_upload_avatar_invalid_type() -> None:
    """POST /avatar with a non-image file returns 422."""
    sb, _ = _make_mock_supabase()

    with patch("app.routes.account.get_supabase_client", return_value=sb):
        resp = client.post(
            "/api/v1/account/avatar",
            files={"file": ("doc.pdf", b"fake-pdf-data", "application/pdf")},
            headers=_make_headers(),
        )

    assert resp.status_code == 422
    assert "unsupported" in resp.json()["detail"].lower()


# ------------------------------------------------------------------
# DELETE /api/v1/account
# ------------------------------------------------------------------


# TC-ACCT-012
def test_delete_account_success() -> None:
    """DELETE /account returns 200 on success."""
    sb, _ = _make_mock_supabase()

    with patch("app.routes.account.get_supabase_client", return_value=sb):
        resp = client.delete("/api/v1/account", headers=_make_headers())

    assert resp.status_code == 200
    assert "deleted" in resp.json()["detail"].lower()


# TC-ACCT-013
def test_delete_account_no_auth() -> None:
    """DELETE /account without Authorization header returns 422."""
    resp = client.delete("/api/v1/account")
    assert resp.status_code == 422


# ------------------------------------------------------------------
# POST /api/v1/account/invite
# ------------------------------------------------------------------

_INVITE_SETTINGS = MagicMock(site_url="https://code-pulse.xyz")


# TC-ACCT-014
def test_invite_user_success() -> None:
    """POST /invite sends an invite and returns 200 with confirmation."""
    sb, _ = _make_mock_supabase()
    sb.auth.admin.invite_user_by_email.return_value = MagicMock()

    with (
        patch("app.routes.account.get_supabase_client", return_value=sb),
        patch("app.routes.account.get_settings", return_value=_INVITE_SETTINGS),
    ):
        resp = client.post(
            "/api/v1/account/invite",
            json={"email": "newuser@example.com"},
            headers=_make_headers(),
        )

    assert resp.status_code == 200
    assert "newuser@example.com" in resp.json()["detail"]
    sb.auth.admin.invite_user_by_email.assert_called_once_with(
        "newuser@example.com",
        options={"redirect_to": "https://code-pulse-six.vercel.app"},
    )


# TC-ACCT-015
def test_invite_user_supabase_error() -> None:
    """POST /invite returns 400 with the Supabase error message on failure."""
    sb, _ = _make_mock_supabase()
    sb.auth.admin.invite_user_by_email.side_effect = Exception(
        "User already registered"
    )

    with (
        patch("app.routes.account.get_supabase_client", return_value=sb),
        patch("app.routes.account.get_settings", return_value=_INVITE_SETTINGS),
    ):
        resp = client.post(
            "/api/v1/account/invite",
            json={"email": "existing@example.com"},
            headers=_make_headers(),
        )

    assert resp.status_code == 400
    assert "User already registered" in resp.json()["detail"]


# TC-ACCT-016
def test_invite_user_no_auth() -> None:
    """POST /invite without Authorization header returns 422."""
    resp = client.post(
        "/api/v1/account/invite",
        json={"email": "newuser@example.com"},
    )
    assert resp.status_code == 422


# ------------------------------------------------------------------
# GET /api/v1/account/export
# ------------------------------------------------------------------


# TC-ACCT-017
def test_export_data_success() -> None:
    """GET /export returns 200 with profile and submissions."""
    sb, _ = _make_mock_supabase()

    # Track which table is being queried to return different data
    table_calls = []

    def _table_side_effect(name):
        table_calls.append(name)
        builder = MagicMock()
        builder.select.return_value = builder
        builder.eq.return_value = builder
        builder.order.return_value = builder

        if name == "profiles":
            builder.execute.return_value = MagicMock(data=[dict(_PROFILE_ROW)])
        elif name == "submissions":
            builder.execute.return_value = MagicMock(data=[dict(_SUBMISSION_ROW)])
        elif name == "analysis_reports":
            builder.execute.return_value = MagicMock(data=[dict(_REPORT_ROW)])
        elif name == "findings":
            builder.execute.return_value = MagicMock(data=[])
        elif name == "predicted_bugs":
            builder.execute.return_value = MagicMock(data=[])
        else:
            builder.execute.return_value = MagicMock(data=[])

        return builder

    sb.table.side_effect = _table_side_effect

    with patch("app.routes.account.get_supabase_client", return_value=sb):
        resp = client.get("/api/v1/account/export", headers=_make_headers())

    assert resp.status_code == 200
    body = resp.json()
    assert "profile" in body
    assert "submissions" in body
    assert body["profile"]["id"] == _USER_ID
    assert body["profile"]["email"] == "test@example.com"
    assert len(body["submissions"]) == 1
    assert body["submissions"][0]["submission_id"] == "sub-001"
    assert body["submissions"][0]["report"]["overall_score"] == 85


# TC-ACCT-018
def test_export_data_no_auth() -> None:
    """GET /export without Authorization header returns 422."""
    resp = client.get("/api/v1/account/export")
    assert resp.status_code == 422
