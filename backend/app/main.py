"""CodePulse Backend — FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

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
