"""Tests for the POST /api/v1/analyze endpoint and auth dependency."""

from fastapi.testclient import TestClient
from jose import jwt

from app.config import Settings, get_settings
from app.main import app

_TEST_JWT_SECRET = "test-secret-key-for-unit-testing-only"


def _override_settings() -> Settings:
    """Return a Settings instance wired to test values (no .env required)."""
    return Settings.model_construct(
        supabase_url="https://test.supabase.co",
        supabase_anon_key="test-anon-key",
        supabase_service_role_key="test-service-role-key",
        supabase_jwt_secret=_TEST_JWT_SECRET,
    )


app.dependency_overrides[get_settings] = _override_settings

client = TestClient(app)


def _make_token(user_id: str = "00000000-0000-0000-0000-000000000001") -> str:
    """Sign a JWT with the claims required by get_current_user."""
    return jwt.encode(
        {
            "sub": user_id,
            "aud": "authenticated",
            "iss": "https://test.supabase.co",
        },
        _TEST_JWT_SECRET,
        algorithm="HS256",
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


def test_health_check() -> None:
    """GET / returns 200 and ok status."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------


def test_analyze_missing_auth_header() -> None:
    """Missing Authorization header returns 422 (required field absent)."""
    response = client.post("/api/v1/analyze", json={"code": "print('hello')"})
    assert response.status_code == 422


def test_analyze_malformed_token() -> None:
    """Garbage token string returns 401."""
    response = client.post(
        "/api/v1/analyze",
        json={"code": "print('hello')"},
        headers={"Authorization": "Bearer this-is-not-a-jwt"},
    )
    assert response.status_code == 401


def test_analyze_wrong_prefix() -> None:
    """Token without 'Bearer ' prefix returns 401."""
    token = _make_token()
    response = client.post(
        "/api/v1/analyze",
        json={"code": "print('hello')"},
        headers={"Authorization": token},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_analyze_valid_token_returns_mock() -> None:
    """Valid JWT returns the mock analysis response."""
    token = _make_token()
    response = client.post(
        "/api/v1/analyze",
        json={"code": "print('hello world')"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "received"
    assert body["lines"] == 42


# ---------------------------------------------------------------------------
# Request validation
# ---------------------------------------------------------------------------


def test_analyze_missing_code_field() -> None:
    """Body missing the 'code' field returns 422."""
    token = _make_token()
    response = client.post(
        "/api/v1/analyze",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
