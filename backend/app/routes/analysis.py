"""Analysis route — ingress endpoint for code submissions."""

import asyncio
import logging

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.analysis import AnalyzeRequest, AnalyzeResponse
from app.services.codebert_validator import validate_predictions
from app.services.engines.python_engine import PythonEngine
from app.services.gpt_predictor import generate_submission_name, predict_bugs
from app.services.persistence_service import (
    PersistenceError,
    persist_analysis,
    reanalyze_submission,
)

logger = logging.getLogger(__name__)

run_static_analysis = PythonEngine.run_static_analysis
compute_score = PythonEngine.compute_score

router = APIRouter(tags=["analysis"])


# FR-ANALYSIS-001
# FR-ANALYSIS-002
# FR-ANALYSIS-003
# FR-REPORT-001
# FR-REPORT-002
# NFR-PERF-001
# NFR-RELI-001
@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    payload: AnalyzeRequest,
    user_id: str = Depends(get_current_user),
) -> AnalyzeResponse:
    """Run static analysis and GPT bug prediction on a code submission.

    Auth required: valid Supabase JWT in the Authorization header.

    Args:
        payload: JSON body containing the ``code`` string.
        user_id: Authenticated user UUID extracted from the JWT.

    Returns:
        An :class:`AnalyzeResponse` with score, summary, static findings,
        and GPT-predicted bugs.
    """
    # 1. Static analysis (sync, CPU-bound but fast enough for request cycle).
    # FR-ANALYSIS-002
    findings, _ = run_static_analysis(payload.code)

    # 2. Predict bugs and generate submission name concurrently.
    # Name generation only needs payload.code — independent of bug results.
    # FR-ANALYSIS-003
    # FR-ANALYSIS-004
    submission_id: str | None = payload.submission_id
    submission_name: str | None = payload.name
    need_name = not submission_id and not submission_name

    if need_name:
        predicted_bugs, submission_name = await asyncio.gather(
            predict_bugs(payload.code, findings),
            generate_submission_name(payload.code),
        )
    else:
        predicted_bugs = await predict_bugs(payload.code, findings)

    # 2b. CodeBERT validation — attaches confidence + flagged to each bug.
    predicted_bugs = await validate_predictions(payload.code, predicted_bugs)

    # 3. Final score incorporates both finding sets.
    # FR-REPORT-001
    overall_score = compute_score(findings, predicted_bugs)
    summary = (
        f"Score {overall_score}/100 — "
        f"{len(findings)} static finding{'s' if len(findings) != 1 else ''}, "
        f"{len(predicted_bugs)} predicted bug{'s' if len(predicted_bugs) != 1 else ''}."
    )

    # 4. Branch: reanalyze existing or create new submission.
    # FR-ANALYSIS-005 (reanalyze path) / FR-HIST-001 (new submission path)
    try:
        if submission_id:
            # Reanalyze — preserves existing name, updates code + results.
            submission_id, submission_name = await reanalyze_submission(
                submission_id=submission_id,
                user_id=user_id,
                code=payload.code,
                overall_score=overall_score,
                summary=summary,
                findings=findings,
                predicted_bugs=predicted_bugs,
            )
        else:
            # Name already generated (or provided) concurrently in step 2.
            submission_id, submission_name = await persist_analysis(
                user_id=user_id,
                code=payload.code,
                overall_score=overall_score,
                summary=summary,
                findings=findings,
                predicted_bugs=predicted_bugs,
                name=submission_name,
            )
    # NFR-RELI-001
    except PersistenceError as exc:
        logger.warning("Persistence failed for user %s: %s", user_id, exc)

    return AnalyzeResponse(
        overall_score=overall_score,
        summary=summary,
        findings=findings,
        predicted_bugs=predicted_bugs,
        submission_id=submission_id,
        name=submission_name,
    )
