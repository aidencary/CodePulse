"""Analysis route — ingress endpoint for code submissions."""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.analysis import AnalyzeRequest, AnalyzeResponse

router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    payload: AnalyzeRequest,
    user_id: str = Depends(get_current_user),
) -> AnalyzeResponse:
    """Receive a code submission and return a mock analysis result.

    Auth required: valid Supabase JWT in the Authorization header.

    Args:
        payload: JSON body containing the ``code`` string.
        user_id: Authenticated user UUID extracted from the JWT.

    Returns:
        A mock AnalyzeResponse while the real engine is under development.
    """
    # TODO: hand off to the analysis engine service in a future story
    return AnalyzeResponse(status="received", lines=42)
