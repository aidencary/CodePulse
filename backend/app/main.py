"""CodePulse Backend — FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import analysis

app = FastAPI(
    title="CodePulse API",
    version="0.1.0",
    description="Secure gateway between the CodePulse frontend and the analysis engine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router, prefix="/api/v1")


@app.get("/", tags=["health"])
async def health_check() -> dict:
    """Return service health status."""
    return {"status": "ok"}
