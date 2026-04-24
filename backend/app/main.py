"""CodePulse Backend — FastAPI application entry point."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.routes import account, analysis, submissions
from app.services.codebert_validator import load_model as load_codebert

logger = logging.getLogger(__name__)

_debug = os.environ.get("DEBUG", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # CodeBERT load failures (including OOM on Render free tier) are
    # non-fatal — the validator no-ops and the analysis pipeline degrades
    # to pre-CodeBERT behavior rather than taking the API down.
    try:
        load_codebert()
    except Exception as exc:
        logger.error("CodeBERT failed to load — validator will pass through: %s", exc)
    yield


app = FastAPI(
    title="CodePulse API",
    version="1.0.0",
    description="Gateway between the CodePulse frontend and the analysis engine.",
    docs_url="/docs" if _debug else None,
    redoc_url="/redoc" if _debug else None,
    lifespan=lifespan,
)


def _build_allowed_origins(raw_origins: str) -> list[str]:
    origins: list[str] = []
    for origin in raw_origins.split(","):
        origin = origin.strip().rstrip("/")
        if origin and origin not in origins:
            origins.append(origin)

    local_dev_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
    ]

    for origin in local_dev_origins:
        if origin not in origins:
            origins.append(origin)

    return origins


_raw_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
_origins = _build_allowed_origins(_raw_origins)
logger.warning("CORS allowed origins: %s", _origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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
app.include_router(account.router, prefix="/api/v1")
app.include_router(submissions.router, prefix="/api/v1")


@app.get("/", tags=["health"])
async def health_check() -> dict:
    """Return service health status."""
    return {"status": "ok"}
