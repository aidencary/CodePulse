"""Pydantic models for the analysis endpoint."""

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Payload sent by the client to the /analyze endpoint."""

    code: str = Field(..., max_length=100_000)


class AnalyzeResponse(BaseModel):
    """Response returned by the /analyze endpoint."""

    status: str
    lines: int
