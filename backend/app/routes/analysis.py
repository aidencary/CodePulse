"""Analysis route — ingress endpoint for code submissions."""

import logging

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.analysis import AnalyzeRequest, AnalyzeResponse
from app.services.analysis_engine import compute_score, run_static_analysis
from app.services.gpt_predictor import generate_submission_name, predict_bugs
from app.services.persistence_service import (
    PersistenceError,
    persist_analysis,
    reanalyze_submission,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])


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
    findings, _ = run_static_analysis(payload.code)

    # 2. GPT bug prediction (async I/O).
    predicted_bugs = await predict_bugs(payload.code, findings)

    # 3. Final score incorporates both finding sets.
    overall_score = compute_score(findings, predicted_bugs)
    summary = (
        f"Score {overall_score}/100 — "
        f"{len(findings)} static finding{'s' if len(findings) != 1 else ''}, "
        f"{len(predicted_bugs)} predicted bug{'s' if len(predicted_bugs) != 1 else ''}."
    )

    # 4. Branch: reanalyze existing or create new submission.
    submission_id: str | None = payload.submission_id
    submission_name: str | None = payload.name

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
            # New submission — generate name if not provided.
            if not submission_name:
                submission_name = await generate_submission_name(payload.code)
            submission_id, submission_name = await persist_analysis(
                user_id=user_id,
                code=payload.code,
                overall_score=overall_score,
                summary=summary,
                findings=findings,
                predicted_bugs=predicted_bugs,
                name=submission_name,
            )
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
