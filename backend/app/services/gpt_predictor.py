"""GPT-based bug prediction service - calls OpenAI to find latent bugs in code."""

import json
import logging

from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.models.analysis import Finding, PredictedBug
from app.services.prompts.python_prompt import build_system_prompt, build_user_message

logger = logging.getLogger(__name__)


# Internal validation model
class GptPrediction(BaseModel):
    """Validated wrapper around the JSON object returned by GPT."""

    predicted_bugs: list[PredictedBug]


# Public API
# FR-ANALYSIS-003
# NFR-RELI-001
async def predict_bugs(
    code: str,
    findings: list[Finding],
    language: str = "python",
) -> list[PredictedBug]:
    """Call the OpenAI Chat Completions API to predict latent bugs in *code*.

    Any API or parsing failure is logged and an empty list is returned so that
    the calling route can still serve static findings to the user.

    Args:
        code: The {language} source code to analyse.
        findings: Static analysis findings already found (to avoid duplication).
        language: The programming language of the code.

    Returns:
        A list of :class:`PredictedBug` objects, or ``[]`` on any failure.
    """
    try:
        from openai import AsyncOpenAI  # local import to simplify mocking

        settings = get_settings()
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        # Build the prompt with the findings summary and user code.
        response = await client.chat.completions.create(
            model=settings.gpt_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": build_system_prompt(findings, language)},
                {"role": "user", "content": build_user_message(code, language)},
            ],
            temperature=0.2,
            max_tokens=2048,
        )

        # Parse and validate the response against our GptPrediction model.
        raw_content = response.choices[0].message.content
        parsed = json.loads(raw_content)
        prediction = GptPrediction.model_validate(parsed)
        logger.debug("GPT returned %d predicted bugs.", len(prediction.predicted_bugs))
        return prediction.predicted_bugs
    # Catch JSON parsing errors and Pydantic validation errors to handle
    # malformed GPT responses gracefully.
    # NFR-RELI-001
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("GPT response failed validation: %s", exc)
        return []
    # NFR-RELI-001
    except Exception as exc:  # noqa: BLE001
        logger.warning("GPT prediction failed: %s", exc)
        return []


# FR-ANALYSIS-004
async def generate_submission_name(code: str) -> str:
    """Ask GPT to generate a short, descriptive name for a code submission.

    Returns a fallback name on any failure.
    """
    try:
        from openai import AsyncOpenAI

        settings = get_settings()
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        response = await client.chat.completions.create(
            model=settings.gpt_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant. Given a "
                        "code snippet, respond with ONLY a short, "
                        "descriptive name (2-5 words) for the code. "
                        "No quotes, no punctuation, no explanation. "
                        "Examples: Fibonacci Calculator, "
                        "CSV Parser, Todo List API"
                    ),
                },
                {"role": "user", "content": code[:2000]},
            ],
            temperature=0.3,
            max_tokens=20,
        )
        name = response.choices[0].message.content.strip().strip("\"'")
        return name if name else "Untitled Submission"
    except Exception as exc:  # noqa: BLE001
        logger.warning("GPT name generation failed: %s", exc)
        return "Untitled Submission"
