"""Integration tests for submissions CRUD endpoints."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from jose import jwt

from app.config import Settings, get_settings
from app.main import app

_TEST_JWT_SECRET = "test-secret-key-for-unit-testing-only"

_USER_ID = "00000000-0000-0000-0000-000000000001"
_OTHER_USER_ID = "00000000-0000-0000-0000-000000000099"
_SUBMISSION_ID = "sub-00000000-0000-0000-0000-000000000001"

_SUBMISSION_ROW = {
    "submission_id": _SUBMISSION_ID,
    "name": "My Analysis",
    "created_at": "2025-06-01T12:00:00+00:00",
    "user_id": _USER_ID,
    "analysis_reports": {"overall_score": 85},
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


def _make_mock_supabase():
    """Build a MagicMock that mimics a Supabase Python client with chaining."""
    sb = MagicMock()

    builder = MagicMock()
    builder.select.return_value = builder
    builder.eq.return_value = builder
    builder.neq.return_value = builder
    builder.update.return_value = builder
    builder.delete.return_value = builder
    builder.insert.return_value = builder
    builder.order.return_value = builder

    builder.execute.return_value = MagicMock(data=[dict(_SUBMISSION_ROW)])
    sb.table.return_value = builder

    return sb, builder


# ------------------------------------------------------------------
# GET /api/v1/submissions
# ------------------------------------------------------------------


def test_list_submissions_success() -> None:
    """GET /submissions returns 200 with an array of submissions."""
    sb, builder = _make_mock_supabase()
    builder.execute.return_value = MagicMock(data=[dict(_SUBMISSION_ROW)])

    with patch("app.routes.submissions.get_supabase_client", return_value=sb):
        resp = client.get("/api/v1/submissions", headers=_make_headers())

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 1
    item = body[0]
    for key in ("submission_id", "name", "created_at", "overall_score"):
        assert key in item, f"Missing key: {key}"
    assert item["overall_score"] == 85


def test_list_submissions_no_auth() -> None:
    """GET /submissions without Authorization header returns 422."""
    resp = client.get("/api/v1/submissions")
    assert resp.status_code == 422


# ------------------------------------------------------------------
# PATCH /api/v1/submissions/{id}
# ------------------------------------------------------------------


def test_rename_submission_success() -> None:
    """PATCH /submissions/{id} renames and returns 200."""
    sb, builder = _make_mock_supabase()

    call_count = {"n": 0}

    def _execute_side_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # Ownership check — select("user_id")
            return MagicMock(data=[{"user_id": _USER_ID}])
        if call_count["n"] == 2:
            # Update returns the updated row
            updated = dict(_SUBMISSION_ROW, name="Renamed")
            return MagicMock(data=[updated])
        if call_count["n"] == 3:
            # Score fetch
            return MagicMock(data=[{"overall_score": 85}])
        return MagicMock(data=[])

    builder.execute.side_effect = _execute_side_effect

    with patch("app.routes.submissions.get_supabase_client", return_value=sb):
        resp = client.patch(
            f"/api/v1/submissions/{_SUBMISSION_ID}",
            json={"name": "Renamed"},
            headers=_make_headers(),
        )

    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"


def test_rename_submission_not_found() -> None:
    """PATCH /submissions/{id} for a missing submission returns 404."""
    sb, builder = _make_mock_supabase()
    builder.execute.return_value = MagicMock(data=[])

    with patch("app.routes.submissions.get_supabase_client", return_value=sb):
        resp = client.patch(
            f"/api/v1/submissions/{_SUBMISSION_ID}",
            json={"name": "Renamed"},
            headers=_make_headers(),
        )

    assert resp.status_code == 404


def test_rename_submission_not_owner() -> None:
    """PATCH /submissions/{id} by a non-owner returns 403."""
    sb, builder = _make_mock_supabase()
    # Ownership check returns a different user
    builder.execute.return_value = MagicMock(data=[{"user_id": _OTHER_USER_ID}])

    with patch("app.routes.submissions.get_supabase_client", return_value=sb):
        resp = client.patch(
            f"/api/v1/submissions/{_SUBMISSION_ID}",
            json={"name": "Renamed"},
            headers=_make_headers(),
        )

    assert resp.status_code == 403


def test_rename_submission_empty_name() -> None:
    """PATCH /submissions/{id} with an empty name returns 422."""
    resp = client.patch(
        f"/api/v1/submissions/{_SUBMISSION_ID}",
        json={"name": ""},
        headers=_make_headers(),
    )
    assert resp.status_code == 422


# ------------------------------------------------------------------
# DELETE /api/v1/submissions/{id}
# ------------------------------------------------------------------


def test_delete_submission_success() -> None:
    """DELETE /submissions/{id} returns 200 on success."""
    sb, builder = _make_mock_supabase()
    # Ownership check
    builder.execute.return_value = MagicMock(data=[{"user_id": _USER_ID}])

    with patch("app.routes.submissions.get_supabase_client", return_value=sb):
        resp = client.delete(
            f"/api/v1/submissions/{_SUBMISSION_ID}",
            headers=_make_headers(),
        )

    assert resp.status_code == 200
    assert "deleted" in resp.json()["detail"].lower()


def test_delete_submission_not_found() -> None:
    """DELETE /submissions/{id} for a missing submission returns 404."""
    sb, builder = _make_mock_supabase()
    builder.execute.return_value = MagicMock(data=[])

    with patch("app.routes.submissions.get_supabase_client", return_value=sb):
        resp = client.delete(
            f"/api/v1/submissions/{_SUBMISSION_ID}",
            headers=_make_headers(),
        )

    assert resp.status_code == 404


def test_delete_submission_not_owner() -> None:
    """DELETE /submissions/{id} by a non-owner returns 403."""
    sb, builder = _make_mock_supabase()
    builder.execute.return_value = MagicMock(data=[{"user_id": _OTHER_USER_ID}])

    with patch("app.routes.submissions.get_supabase_client", return_value=sb):
        resp = client.delete(
            f"/api/v1/submissions/{_SUBMISSION_ID}",
            headers=_make_headers(),
        )

    assert resp.status_code == 403


# ------------------------------------------------------------------
# PATCH /api/v1/submissions/{id}/pin
# ------------------------------------------------------------------


def test_toggle_pin_success() -> None:
    """PATCH /submissions/{id}/pin toggles pin and returns 200."""
    sb, builder = _make_mock_supabase()

    call_count = {"n": 0}

    def _execute_side_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # Ownership check — unpinned submission
            return MagicMock(data=[{"user_id": _USER_ID, "pinned_at": None}])
        # Update call
        return MagicMock(data=[])

    builder.execute.side_effect = _execute_side_effect

    with patch("app.routes.submissions.get_supabase_client", return_value=sb):
        resp = client.patch(
            f"/api/v1/submissions/{_SUBMISSION_ID}/pin",
            headers=_make_headers(),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["pinned"] is True
    assert body["pinned_at"] is not None


def test_toggle_unpin_success() -> None:
    """PATCH /submissions/{id}/pin unpins a pinned submission."""
    sb, builder = _make_mock_supabase()

    call_count = {"n": 0}

    def _execute_side_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return MagicMock(
                data=[
                    {
                        "user_id": _USER_ID,
                        "pinned_at": "2025-06-01T12:00:00+00:00",
                    }
                ]
            )
        return MagicMock(data=[])

    builder.execute.side_effect = _execute_side_effect

    with patch("app.routes.submissions.get_supabase_client", return_value=sb):
        resp = client.patch(
            f"/api/v1/submissions/{_SUBMISSION_ID}/pin",
            headers=_make_headers(),
        )

    assert resp.status_code == 200
    assert resp.json()["pinned"] is False


def test_toggle_pin_not_found() -> None:
    """PATCH /submissions/{id}/pin for a missing submission returns 404."""
    sb, builder = _make_mock_supabase()
    builder.execute.return_value = MagicMock(data=[])

    with patch("app.routes.submissions.get_supabase_client", return_value=sb):
        resp = client.patch(
            f"/api/v1/submissions/{_SUBMISSION_ID}/pin",
            headers=_make_headers(),
        )

    assert resp.status_code == 404


def test_toggle_pin_not_owner() -> None:
    """PATCH /submissions/{id}/pin by a non-owner returns 403."""
    sb, builder = _make_mock_supabase()
    builder.execute.return_value = MagicMock(
        data=[{"user_id": _OTHER_USER_ID, "pinned_at": None}]
    )

    with patch("app.routes.submissions.get_supabase_client", return_value=sb):
        resp = client.patch(
            f"/api/v1/submissions/{_SUBMISSION_ID}/pin",
            headers=_make_headers(),
        )

    assert resp.status_code == 403
