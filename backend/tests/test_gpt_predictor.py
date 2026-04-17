"""Unit tests for the GPT bug prediction service."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.services.gpt_predictor as gpt_predictor_module
from app.config import Settings
from app.models.analysis import Finding, PredictedBug
from app.services.gpt_predictor import predict_bugs
from app.services.prompts.python_prompt import build_user_message


@pytest.fixture(autouse=True)
def reset_openai_singleton():
    """Reset the module-level OpenAI client singleton before each test."""
    gpt_predictor_module._openai_client = None
    yield
    gpt_predictor_module._openai_client = None


# Shared fixtures
_MOCK_SETTINGS = Settings.model_construct(
    supabase_url="https://test.supabase.co",
    supabase_anon_key="test-anon-key",
    supabase_service_role_key="test-service-role-key",
    supabase_jwt_secret="test-secret",
    openai_api_key="test-openai-key",
    gpt_model="gpt-4o-mini",
)

_VALID_BUG = {
    "line_number": 10,
    "bug_type": "null_dereference",
    "severity": "high",
    "description": "Variable may be None.",
    "suggested_fix": "Add a None check before use.",
}

_VALID_RESPONSE_JSON = json.dumps({"predicted_bugs": [_VALID_BUG]})
_EMPTY_RESPONSE_JSON = json.dumps({"predicted_bugs": []})


def _make_openai_response(content: str) -> MagicMock:
    """Build a minimal mock of the openai v1.x ChatCompletion response."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


# Happy path
@pytest.mark.asyncio
# TC-ANALYSIS-070
async def test_returns_predicted_bugs_on_valid_response() -> None:
    """A valid GPT JSON response is parsed into PredictedBug objects."""
    mock_response = _make_openai_response(_VALID_RESPONSE_JSON)
    mock_create = AsyncMock(return_value=mock_response)

    with (
        patch("app.services.gpt_predictor.get_settings", return_value=_MOCK_SETTINGS),
        patch("app.services.gpt_predictor.AsyncOpenAI") as MockClient,
    ):
        MockClient.return_value.chat.completions.create = mock_create
        result = await predict_bugs("x = None\nprint(x.value)", [])

    assert len(result) == 1
    bug = result[0]
    assert isinstance(bug, PredictedBug)
    assert bug.bug_type == "null_dereference"
    assert bug.severity == "high"
    assert bug.line_number == 10


@pytest.mark.asyncio
# TC-ANALYSIS-071
async def test_returns_empty_list_on_empty_predicted_bugs_array() -> None:
    """GPT response with an empty predicted_bugs array returns []."""
    mock_response = _make_openai_response(_EMPTY_RESPONSE_JSON)
    mock_create = AsyncMock(return_value=mock_response)

    with (
        patch("app.services.gpt_predictor.get_settings", return_value=_MOCK_SETTINGS),
        patch("app.services.gpt_predictor.AsyncOpenAI") as MockClient,
    ):
        MockClient.return_value.chat.completions.create = mock_create
        result = await predict_bugs("x = 1", [])

    assert result == []


# Failure / fallback paths
@pytest.mark.asyncio
# TC-ANALYSIS-072
async def test_returns_empty_list_on_api_error() -> None:
    """An OpenAI API error results in an empty list (no crash)."""
    import openai

    mock_create = AsyncMock(side_effect=openai.OpenAIError("rate limit"))

    with (
        patch("app.services.gpt_predictor.get_settings", return_value=_MOCK_SETTINGS),
        patch("app.services.gpt_predictor.AsyncOpenAI") as MockClient,
    ):
        MockClient.return_value.chat.completions.create = mock_create
        result = await predict_bugs("x = 1", [])

    assert result == []


@pytest.mark.asyncio
# TC-ANALYSIS-073
async def test_returns_empty_list_on_malformed_json() -> None:
    """A response that is not valid JSON results in an empty list."""
    mock_response = _make_openai_response("not json at all")
    mock_create = AsyncMock(return_value=mock_response)

    with (
        patch("app.services.gpt_predictor.get_settings", return_value=_MOCK_SETTINGS),
        patch("app.services.gpt_predictor.AsyncOpenAI") as MockClient,
    ):
        MockClient.return_value.chat.completions.create = mock_create
        result = await predict_bugs("x = 1", [])

    assert result == []


@pytest.mark.asyncio
# TC-ANALYSIS-074
async def test_returns_empty_list_on_schema_validation_failure() -> None:
    """Valid JSON with the wrong schema results in an empty list."""
    bad_json = json.dumps({"bugs": [{"wrong_field": "value"}]})
    mock_response = _make_openai_response(bad_json)
    mock_create = AsyncMock(return_value=mock_response)

    with (
        patch("app.services.gpt_predictor.get_settings", return_value=_MOCK_SETTINGS),
        patch("app.services.gpt_predictor.AsyncOpenAI") as MockClient,
    ):
        MockClient.return_value.chat.completions.create = mock_create
        result = await predict_bugs("x = 1", [])

    assert result == []


# Prompt construction
@pytest.mark.asyncio
# TC-ANALYSIS-075
async def test_system_prompt_includes_static_findings() -> None:
    """Static findings are summarised in the system prompt sent to GPT."""
    findings = [
        Finding(
            issue_type="bare_except",
            line_number=5,
            severity="Med",
            message="Bare except clause.",
        )
    ]
    mock_response = _make_openai_response(_EMPTY_RESPONSE_JSON)
    mock_create = AsyncMock(return_value=mock_response)

    with (
        patch("app.services.gpt_predictor.get_settings", return_value=_MOCK_SETTINGS),
        patch("app.services.gpt_predictor.AsyncOpenAI") as MockClient,
    ):
        MockClient.return_value.chat.completions.create = mock_create
        await predict_bugs("try:\n    pass\nexcept:\n    pass", findings)

    call_kwargs = mock_create.call_args.kwargs
    system_message = next(
        m["content"] for m in call_kwargs["messages"] if m["role"] == "system"
    )
    assert "bare_except" in system_message


# User message format
# TC-ANALYSIS-076
def test_user_message_prefixes_each_line_with_line_number() -> None:
    """Each line of the code is prefixed with its 1-based line number."""
    code = "x = 1\ny = 2\nz = 3"
    message = build_user_message(code, "python")
    assert "1: x = 1" in message
    assert "2: y = 2" in message
    assert "3: z = 3" in message


# TC-ANALYSIS-077
def test_user_message_preserves_blank_lines() -> None:
    """Blank lines are numbered so GPT line numbers match the editor."""
    code = "x = 1\n\nz = 3"
    message = build_user_message(code, "python")
    assert "1: x = 1" in message
    assert "2: " in message
    assert "3: z = 3" in message
