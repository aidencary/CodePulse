"""Pydantic models for the analysis endpoint."""

from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Payload sent by the client to the /analyze endpoint."""

    code: str = Field(..., max_length=100_000)
    name: str | None = Field(None, max_length=100)
    submission_id: str | None = Field(None, description="Reanalyze existing submission")


class Finding(BaseModel):
    """A single static-analysis finding."""

    issue_type: str
    line_number: int
    severity: Literal["Low", "Med", "High"]
    message: str


class PredictedBug(BaseModel):
    """A single GPT-predicted bug, optionally validated by CodeBERT."""

    line_number: int | None
    bug_type: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    suggested_fix: str
    confidence: float | None = None
    flagged: bool = False


class AnalyzeResponse(BaseModel):
    """Response returned by the /analyze endpoint."""

    overall_score: int
    summary: str
    findings: list[Finding]
    predicted_bugs: list[PredictedBug]
    submission_id: str | None = None
    name: str | None = None


class SubmissionListItem(BaseModel):
    """A single submission in the user's submission list."""

    submission_id: str
    name: str | None = None
    created_at: str
    overall_score: int | None = None
    pinned_at: str | None = None


class SubmissionRenameRequest(BaseModel):
    """Payload for renaming a submission."""

    name: str = Field(..., min_length=1, max_length=100)
