# CodePulse Backend

Python FastAPI backend for the CodePulse code quality and bug prediction dashboard.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Python 3.x, FastAPI |
| Database | Supabase (PostgreSQL + Auth + RLS) |
| Auth | Supabase JWT verification |
| Analysis Engine | Static analysis + ML (planned) |
| API Docs | Swagger / OpenAPI (available at `/docs` when `DEBUG=true`) |

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point, CORS, router mount
│   ├── config.py               # Pydantic Settings loaded from .env
│   ├── dependencies.py         # get_current_user — Supabase JWT auth
│   ├── models/
│   │   └── analysis.py         # AnalyzeRequest / AnalyzeResponse
│   └── routes/
│       └── analysis.py         # POST /api/v1/analyze
├── engine/                     # Code analysis pipeline (planned)
│   ├── ast_parser.py
│   ├── static_analyzer.py
│   └── ai_model_loader.py
├── tests/
│   ├── test_placeholder.py
│   └── test_analyze_endpoint.py
├── database/
│   └── schema.sql              # Supabase PostgreSQL schema (source of truth)
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Database Schema

Defined in `database/schema.sql`. Run in the Supabase SQL Editor to apply.

| Table | Description |
|-------|-------------|
| `auth.users` | Managed by Supabase Auth — do not create manually |
| `profiles` | 1:1 with `auth.users`; stores username, role, profile picture |
| `submissions` | User code submissions with `user_id` FK to `auth.users` |
| `analysis_reports` | Analysis results linked to a submission |
| `findings` | Individual issues found in a report |
| `actionable_fixes` | Suggested fix for a finding |

Row Level Security (RLS) is enabled on all tables. Users can only access their own data.

---

## Authentication

The backend will validate Supabase JWTs on all protected endpoints. The frontend sends the token in the `Authorization` header:

```
Authorization: Bearer <session.access_token>
```

The backend verifies the JWT using the Supabase secret and extracts `auth.uid()` to scope all database queries to the requesting user.

---

## Security

Security is enforced at multiple layers so that no single failure exposes user data.

### 1. Supabase Auth — Identity
All authentication is delegated to Supabase Auth. Passwords are hashed and stored internally by Supabase using bcrypt — they are never stored in the application database. The backend never handles raw credentials.

### 2. JWT Verification — Request Authentication
Every request to a protected endpoint must include a valid Supabase JWT in the `Authorization` header. The backend verifies the token's signature using the Supabase JWT secret before any business logic runs. Expired or tampered tokens are rejected with `401 Unauthorized`.

### 3. Row Level Security (RLS) — Data Isolation
All five database tables have RLS enabled. Even if a bug in application code constructs an overly broad query, the database enforces that users can only read and write rows where `user_id = auth.uid()`. User A cannot access User B's submissions, reports, findings, or fixes — at the database level.

| Table | Policy |
|-------|--------|
| `profiles` | SELECT / INSERT / UPDATE / DELETE restricted to own row (`id = auth.uid()`) |
| `submissions` | SELECT / INSERT / DELETE restricted to own rows (`user_id = auth.uid()`) |
| `analysis_reports` | SELECT restricted via submission ownership chain |
| `findings` | SELECT restricted via report → submission ownership chain |
| `actionable_fixes` | SELECT restricted via finding → report → submission ownership chain |

### 4. Service Role Key — Privileged Operations
The `SUPABASE_SERVICE_ROLE_KEY` bypasses RLS and is reserved for trusted server-side operations only (e.g. the analysis engine writing results). It is stored exclusively in `backend/.env`, never sent to the frontend, and never committed to version control.

### 5. Input Validation — API Boundaries
All data entering the API is validated using Pydantic models before it reaches the service layer. User-submitted code is treated as untrusted input and is never executed by the server.

### 6. Secrets Management
All credentials are stored in environment variables loaded from `.env`. The `.env` file is listed in `.gitignore` and is never committed. See `.env.example` for the required variable names.

---

## Local Setup

### Prerequisites

- Python 3.11+
- A configured Supabase project (see `database/schema.sql`)

### Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate        # PowerShell: venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env            # Fill in your Supabase credentials
uvicorn app.main:app --reload   # Runs at http://localhost:8000
```

### Environment Variables

| Variable | Required | Where to find it |
|----------|----------|-----------------|
| `SUPABASE_URL` | Yes | Supabase Dashboard → Settings → API → Project URL |
| `SUPABASE_ANON_KEY` | Yes | Supabase Dashboard → Settings → API → `anon` key |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase Dashboard → Settings → API → `service_role` key |
| `SUPABASE_JWT_SECRET` | Yes | Supabase Dashboard → Settings → API → JWT Secret |
| `DEBUG` | No | Set to `true` locally to enable `/docs` and `/redoc`; omit in production |

Copy `.env.example` to `.env` and fill in the values. Never commit `.env`.

### Docker

```bash
cd backend
docker build -t codepulse-backend .
docker run -p 8000:8000 --env-file .env codepulse-backend
```

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | None | Health check → `{"status": "ok"}` |
| `POST` | `/api/v1/analyze` | Bearer JWT | Submit code for analysis (mock response) |

Full API docs available at `http://localhost:8000/docs` when running locally with `DEBUG=true`. Disabled in production.

---

## Testing

Tests use [pytest](https://pytest.org). Run from the `backend/` directory.

```bash
pip install -r requirements.txt
pytest tests/ -v
```

As backend routes and services are implemented, add a corresponding test file in `tests/` for each service module. See `tests/test_placeholder.py` as a reference starting point.

---

## CI/CD

The backend CI workflow runs automatically on every push and pull request to `main` that touches `backend/**`.

**Workflow:** `.github/workflows/backend-ci.yml`

| Step | Command |
|------|---------|
| Format check | `black --check .` |
| Lint | `flake8 .` |
| Test | `pytest tests/ -v` |

A pull request cannot be merged if any step fails. All new code must be Black-formatted and pass flake8 before opening a PR.

---

## Implementation Status

| Feature | Status |
|---------|--------|
| Database schema + RLS | Done |
| Environment config (`app/config.py`) | Done |
| FastAPI app scaffold (`app/main.py`) | Done |
| JWT auth dependency (`app/dependencies.py`) | Done |
| `POST /api/v1/analyze` — mock response | Done |
| Dockerfile | Done |
| Analysis engine integration (`engine/`) | Not started |
| Submission persistence to Supabase | Not started |
| Results endpoints | Not started |
