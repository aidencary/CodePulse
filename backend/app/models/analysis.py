"""Pydantic models for the analysis endpoint."""

from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Payload sent by the client to the /analyze endpoint."""

    code: str = Field(..., max_length=100_000)


class Finding(BaseModel):
    """A single static-analysis finding."""

    issue_type: str
    line_number: int
    severity: Literal["Low", "Med", "High"]
    message: str


class PredictedBug(BaseModel):
    """A single GPT-predicted bug."""

    line_number: int | None
    bug_type: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    suggested_fix: str


class AnalyzeResponse(BaseModel):
    """Response returned by the /analyze endpoint."""

    overall_score: int
    summary: str
    findings: list[Finding]
    predicted_bugs: list[PredictedBug]
    submission_id: str | None = None
