"""CodePulse Backend — FastAPI application entry point."""

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.routes import analysis

_debug = os.environ.get("DEBUG", "false").lower() == "true"

app = FastAPI(
    title="CodePulse API",
    version="0.1.0",
    description="Gateway between the CodePulse frontend and the analysis engine.",
    docs_url="/docs" if _debug else None,
    redoc_url="/redoc" if _debug else None,
)

_raw_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
_origins = [o.strip() for o in _raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


app.include_router(analysis.router, prefix="/api/v1")


@app.get("/", tags=["health"])
async def health_check() -> dict:
    """Return service health status."""
    return {"status": "ok"}
