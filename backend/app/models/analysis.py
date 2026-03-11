"""Pydantic models for the analysis endpoint."""

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    """Payload sent by the client to the /analyze endpoint."""

    code: str


class AnalyzeResponse(BaseModel):
    """Response returned by the /analyze endpoint."""

    status: str
    lines: int
