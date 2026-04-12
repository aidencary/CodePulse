"""Integration tests for POST /api/v1/analyze with real services mocked."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import Settings, get_settings
from app.main import app
from app.models.analysis import Finding, PredictedBug
from app.services.persistence_service import PersistenceError

_TEST_JWT_SECRET = "test-secret-key-for-unit-testing-only"


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


# Inject test settings so the route uses them instead of the real .env.
app.dependency_overrides[get_settings] = _override_settings

client = TestClient(app)


def _make_token(user_id: str = "00000000-0000-0000-0000-000000000001") -> str:
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


_SAMPLE_CODE = "def foo():\n    pass\n"
_MOCK_FINDING = Finding(
    issue_type="missing_docstring",
    line_number=1,
    severity="Low",
    message="Function 'foo' is missing a docstring.",
)
_MOCK_BUG = PredictedBug(
    line_number=None,
    bug_type="null_dereference",
    severity="medium",
    description="Possible null dereference.",
    suggested_fix="Add a None check.",
)


def _make_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_make_token()}"}


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------


# TC-ANALYSIS-078
def test_analyze_returns_correct_shape() -> None:
    """Response has all required top-level keys."""
    with (
        patch(
            "app.routes.analysis.run_static_analysis",
            return_value=([_MOCK_FINDING], 98),
        ),
        patch(
            "app.routes.analysis.predict_bugs",
            new=AsyncMock(return_value=[_MOCK_BUG]),
        ),
        patch(
            "app.routes.analysis.generate_submission_name",
            new=AsyncMock(return_value="Test Submission"),
        ),
        patch(
            "app.routes.analysis.persist_analysis",
            new=AsyncMock(return_value=("sub-uuid-1234", "Test Submission")),
        ),
    ):
        resp = client.post(
            "/api/v1/analyze",
            json={"code": _SAMPLE_CODE},
            headers=_make_headers(),
        )

    assert resp.status_code == 200
    body = resp.json()
    required_keys = (
        "overall_score",
        "summary",
        "findings",
        "predicted_bugs",
        "submission_id",
    )
    for key in required_keys:
        assert key in body, f"Missing key: {key}"


# TC-ANALYSIS-079
def test_analyze_score_in_range() -> None:
    """overall_score is between 0 and 100 inclusive."""
    with (
        patch("app.routes.analysis.run_static_analysis", return_value=([], 100)),
        patch("app.routes.analysis.predict_bugs", new=AsyncMock(return_value=[])),
        patch(
            "app.routes.analysis.generate_submission_name",
            new=AsyncMock(return_value="Test Submission"),
        ),
        patch(
            "app.routes.analysis.persist_analysis",
            new=AsyncMock(return_value=("sub-1", "Test Submission")),
        ),
    ):
        resp = client.post(
            "/api/v1/analyze",
            json={"code": "x = 1"},
            headers=_make_headers(),
        )

    body = resp.json()
    assert 0 <= body["overall_score"] <= 100


# TC-ANALYSIS-080
def test_analyze_findings_have_required_fields() -> None:
    """Each finding contains issue_type, line_number, severity, and message."""
    with (
        patch(
            "app.routes.analysis.run_static_analysis",
            return_value=([_MOCK_FINDING], 98),
        ),
        patch("app.routes.analysis.predict_bugs", new=AsyncMock(return_value=[])),
        patch(
            "app.routes.analysis.generate_submission_name",
            new=AsyncMock(return_value="Test Submission"),
        ),
        patch(
            "app.routes.analysis.persist_analysis",
            new=AsyncMock(return_value=("sub-1", "Test Submission")),
        ),
    ):
        resp = client.post(
            "/api/v1/analyze",
            json={"code": _SAMPLE_CODE},
            headers=_make_headers(),
        )

    for finding in resp.json()["findings"]:
        for field in ("issue_type", "line_number", "severity", "message"):
            assert field in finding


# TC-ANALYSIS-081
def test_analyze_predicted_bugs_have_required_fields() -> None:
    """Each predicted bug contains all required fields."""
    with (
        patch("app.routes.analysis.run_static_analysis", return_value=([], 100)),
        patch(
            "app.routes.analysis.predict_bugs",
            new=AsyncMock(return_value=[_MOCK_BUG]),
        ),
        patch(
            "app.routes.analysis.generate_submission_name",
            new=AsyncMock(return_value="Test Submission"),
        ),
        patch(
            "app.routes.analysis.persist_analysis",
            new=AsyncMock(return_value=("sub-1", "Test Submission")),
        ),
    ):
        resp = client.post(
            "/api/v1/analyze",
            json={"code": _SAMPLE_CODE},
            headers=_make_headers(),
        )

    for bug in resp.json()["predicted_bugs"]:
        for field in ("bug_type", "severity", "description", "suggested_fix"):
            assert field in bug
        # New CodeBERT validation fields are always present (with defaults).
        assert "confidence" in bug
        assert "flagged" in bug


# TC-ANALYSIS-081b — CodeBERT validation
def test_analyze_flagged_bug_does_not_lower_score() -> None:
    """When validate_predictions flags a bug, compute_score skips its penalty."""
    flagged_bug = _MOCK_BUG.model_copy(
        update={"confidence": 0.1, "flagged": True, "severity": "critical"}
    )
    with (
        patch("app.routes.analysis.run_static_analysis", return_value=([], 100)),
        patch(
            "app.routes.analysis.predict_bugs",
            new=AsyncMock(return_value=[_MOCK_BUG]),
        ),
        patch(
            "app.routes.analysis.validate_predictions",
            new=AsyncMock(return_value=[flagged_bug]),
        ),
        patch(
            "app.routes.analysis.generate_submission_name",
            new=AsyncMock(return_value="Test Submission"),
        ),
        patch(
            "app.routes.analysis.persist_analysis",
            new=AsyncMock(return_value=("sub-1", "Test Submission")),
        ),
    ):
        resp = client.post(
            "/api/v1/analyze",
            json={"code": _SAMPLE_CODE},
            headers=_make_headers(),
        )

    body = resp.json()
    assert body["overall_score"] == 100  # flagged critical bug contributes nothing
    assert body["predicted_bugs"][0]["flagged"] is True
    assert body["predicted_bugs"][0]["confidence"] == pytest.approx(0.1)


# ---------------------------------------------------------------------------
# Resilience
# ---------------------------------------------------------------------------


# TC-ANALYSIS-082
def test_analyze_persistence_failure_still_returns_200() -> None:
    """A PersistenceError does not cause the endpoint to fail."""
    with (
        patch("app.routes.analysis.run_static_analysis", return_value=([], 100)),
        patch("app.routes.analysis.predict_bugs", new=AsyncMock(return_value=[])),
        patch(
            "app.routes.analysis.persist_analysis",
            new=AsyncMock(side_effect=PersistenceError("db down")),
        ),
    ):
        resp = client.post(
            "/api/v1/analyze",
            json={"code": "x = 1"},
            headers=_make_headers(),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "overall_score" in body
    assert body["submission_id"] is None


# ---------------------------------------------------------------------------
# Request validation
# ---------------------------------------------------------------------------


# TC-ANALYSIS-083
def test_analyze_code_too_long_returns_422() -> None:
    """Code exceeding 100 000 characters returns 422."""
    resp = client.post(
        "/api/v1/analyze",
        json={"code": "x" * 100_001},
        headers=_make_headers(),
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


# NFR-SEC-002
def test_analyze_rate_limit_returns_429_after_threshold() -> None:
    """The 11th authenticated /analyze call in a minute returns 429."""
    from app.limiter import limiter

    limiter.reset()
    limiter.enabled = True
    try:
        with (
            patch(
                "app.routes.analysis.run_static_analysis",
                return_value=([], 100),
            ),
            patch(
                "app.routes.analysis.predict_bugs",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "app.routes.analysis.generate_submission_name",
                new=AsyncMock(return_value="Test"),
            ),
            patch(
                "app.routes.analysis.persist_analysis",
                new=AsyncMock(return_value=("submission-id", "Test")),
            ),
        ):
            headers = _make_headers()
            for _ in range(10):
                resp = client.post(
                    "/api/v1/analyze",
                    json={"code": _SAMPLE_CODE},
                    headers=headers,
                )
                assert resp.status_code == 200
            resp = client.post(
                "/api/v1/analyze",
                json={"code": _SAMPLE_CODE},
                headers=headers,
            )
            assert resp.status_code == 429
    finally:
        limiter.reset()
        limiter.enabled = False
