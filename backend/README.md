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
| API Docs | Swagger / OpenAPI (auto-generated at `/docs`) |

---

## Project Structure

```
backend/
├── app/                        # Main application (to be created)
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Environment/configuration settings
│   ├── models/                 # Pydantic models
│   ├── routes/                 # API route handlers (thin layer)
│   ├── services/               # Business logic layer
│   └── utils/                  # Shared utility functions
├── engine/                     # Code analysis pipeline (to be created)
│   ├── ast_parser.py           # AST-based code parsing
│   ├── static_analyzer.py      # Static analysis rules
│   └── ai_model_loader.py      # ML model inference
├── tests/                      # Backend test suite
└── database/
    └── schema.sql              # Supabase PostgreSQL schema (source of truth)
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
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Fill in your Supabase credentials
uvicorn app.main:app --reload   # Runs at http://localhost:8000
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase publishable key (for user-context queries) |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase secret key (server-side only — never expose) |
| `DATABASE_URL` | Direct PostgreSQL connection string |

Copy `.env.example` to `.env` and fill in the values. Never commit `.env`.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| — | — | No endpoints implemented yet |

Full API docs will be available at `http://localhost:8000/docs` once the server is running.

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
| Environment config | Done |
| FastAPI app scaffold | Not started |
| JWT authentication middleware | Not started |
| Submission endpoint | Not started |
| Analysis engine integration | Not started |
| Results endpoints | Not started |
