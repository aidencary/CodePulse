# CLAUDE.md — CodePulse AI Assistant Guide

This file provides AI assistants (Claude, Copilot, etc.) with the context needed to work effectively in this repository.

---


## Project Overview

**CodePulse** is a code quality and bug prediction dashboard. Users paste code into a live editor and receive:

- A **code quality score** (0–100)
- **Standards compliance** findings (deviations from best practices)
- **Bug predictions** via machine learning
- **Actionable fixes** with original/suggested code snippets and rationale

The system is in **early development** — the architecture, standards, and database schema are established, but most implementation files do not yet exist.

---

## Tech Stack

| Layer        | Technology                                              |
|--------------|---------------------------------------------------------|
| Frontend     | JavaScript (ES6+), React (functional components/Hooks)  |
| Backend      | Python 3.x, FastAPI                                     |
| Database     | Supabase (PostgreSQL + Auth + RLS)                      |
| ML/Analysis  | Machine learning libraries (TBD), static analysis tools (TBD) |
| CI/CD        | Git, GitHub, GitHub Actions (planned)                   |

---

## Repository Structure

```
CodePulse/
├── backend/                    # Python FastAPI backend
│   ├── app/                    # Main application (to be created)
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI entry point
│   │   ├── config.py           # Configuration/env settings
│   │   ├── models/             # SQLAlchemy or Pydantic models
│   │   ├── routes/             # API route handlers (thin layer)
│   │   ├── services/           # Business logic layer
│   │   └── utils/              # Shared utility functions
│   ├── engine/                 # Code analysis pipeline (to be created)
│   │   ├── ast_parser.py       # AST-based code parsing
│   │   ├── static_analyzer.py  # Static analysis rules
│   │   └── ai_model_loader.py  # ML model inference
│   ├── tests/                  # Backend test suite
│   ├── database/
│   │   └── schema.sql          # PostgreSQL schema (source of truth)
│   ├── requirements.txt        # Python dependencies (to be created)
│   └── .env.example            # Env variable template (to be created)
│
├── frontend/                   # React frontend
│   ├── public/                 # Static assets
│   ├── src/
│   │   ├── components/         # Reusable React components (PascalCase files)
│   │   ├── pages/              # Page-level components
│   │   ├── services/           # API call functions (camelCase files)
│   │   ├── utils/              # Utility/helper functions
│   │   ├── styles/             # CSS/styling files
│   │   ├── App.js              # Root component
│   │   └── index.js            # Entry point
│   ├── package.json            # Node dependencies (to be created)
│   └── .env.example            # Env variable template (to be created)
│
├── docs/                       # Architecture diagrams and specs
│   ├── CodePulse Class Diagram.drawio.png
│   ├── CodePulse_ER_Diagram.png
│   ├── CodePulse Sequence Diagram.png
│   ├── CodePulse Engine Pipeline Flowchart.png
│   ├── CodePulse_Design_&_Architecture.pdf
│   └── CodePulse_Requirements_Analysis.pdf
│
├── README.md                   # Project overview (user-facing)
├── STANDARDS.md                # Full coding standards reference
└── CLAUDE.md                   # This file
```

---

## Documentation

- Constantly be updating documentation across READMEs

## Database Schema

Defined in `backend/database/schema.sql`. All primary keys are UUIDs. CASCADE deletes are set for child records.

```
auth.users  ← managed by Supabase Auth (do NOT create manually)
  id (UUID PK) | email | ...

profiles  ← 1:1 with auth.users, auto-created on signup via trigger
  id (UUID PK → auth.users) | username (UNIQUE) | role (default: 'developer')
  profile_picture | created_at

submissions
  submission_id (UUID PK) | user_id (FK → auth.users) | code (TEXT) | created_at

analysis_reports
  report_id (UUID PK) | submission_id (UNIQUE FK → submissions)
  overall_score (INT 0–100) | summary (TEXT)

findings
  finding_id (UUID PK) | report_id (FK → analysis_reports)
  issue_type | line_number | line_severity ('Low' | 'Med' | 'High') | message

actionable_fixes
  fix_id (UUID PK) | finding_id (UNIQUE FK → findings)
  original_snippet | suggested_snippet | rationale | tags (TEXT[])
```

**Data flow:** User submits code → `submissions` row created → analysis pipeline runs → `analysis_reports` row created → zero or more `findings` rows → each finding may have one `actionable_fixes` row.

---

## API Design

- FastAPI backend serves a RESTful API
- Swagger/OpenAPI docs auto-generated at `/docs`
- Routes are thin: delegate all logic to the `services/` layer
- Use `async/await` for all I/O-bound operations

---

## Coding Conventions

### Frontend (JavaScript/React)

| Item               | Convention                       |
|--------------------|----------------------------------|
| Component files    | PascalCase (`UserProfile.js`)    |
| Utility files      | camelCase (`apiClient.js`)       |
| Component names    | PascalCase (`UserProfile`)       |
| Variables/functions| camelCase (`fetchUserData`)      |
| Constants          | UPPER_SNAKE_CASE (`API_BASE_URL`)|

- Use **ES6+** syntax (arrow functions, destructuring, spread, optional chaining)
- Use **functional components with Hooks** only — no class components
- One component per file; max **300 lines** per component file — split if larger
- Use **prop-types or TypeScript** for type checking
- Avoid inline styles; use **CSS modules or styled-components**
- Use `useMemo` for expensive computations; implement error boundaries in production
- Use `async/await` for async operations
- Add **JSDoc comments** for complex functions
- Separate **presentational** (dumb) and **container** (smart) components
- Use `index.js` barrel exports for clean imports

### Backend (Python)

| Item             | Convention                          |
|------------------|-------------------------------------|
| Files/modules    | snake_case (`user_service.py`)      |
| Classes          | PascalCase (`UserModel`)            |
| Functions/vars   | snake_case (`get_user_data`)        |
| Constants        | UPPER_SNAKE_CASE (`DATABASE_URL`)   |
| Private methods  | Underscore prefix (`_validate_token`)|

- Follow **PEP 8**; max line length **88 characters** (Black formatter default)
- Use **type hints** on all function parameters and return values
- Write **docstrings** for all classes, functions, and modules
- Use **virtual environments** for dependency isolation
- Validate all external input at API boundaries
- Use environment variables for all configuration — never hardcode secrets
- Use custom exception classes for domain errors
- Log all important operations and errors
- Use `async/await` for I/O-bound operations
- Follow **DRY** — extract shared logic to `utils/` or `services/`
- Keep routes thin: business logic belongs in `services/`
- Write **unit tests** for all business logic in `services/`

---

## Security Standards
- All API endpoints must have authentication checks
- Never trust raw user input — validate before passing to analysis engines
- No hardcoded secrets; use environment variables only
- Supabase queries must respect Row Level Security

### Known Security Issues (fix before production)

**1. CORS misconfiguration — `backend/app/main.py`**
`allow_origins=["*"]` combined with `allow_credentials=True` is a spec violation — browsers will block credentialed cross-origin requests. Lock the origin list:
- Dev: `allow_origins=["http://localhost:3000"]`
- Prod: read from an env var (`ALLOWED_ORIGINS`)

**2. JWT audience not verified — `backend/app/dependencies.py`**
`options={"verify_aud": False}` skips the `aud` claim check. Add `audience="authenticated"` to `jwt.decode()` to match what Supabase puts in every token.

**3. Unbounded `code` field — `backend/app/models/analysis.py`**
`code: str` has no max length. Add `code: str = Field(..., max_length=100_000)` before the analysis engine is wired up.

**4. DOMPurify XSS in `monaco-editor` (npm) — `frontend/`**
`monaco-editor >= 0.54.0` depends on a vulnerable DOMPurify version. Run `npm audit fix` in `frontend/` to resolve without breaking changes.

**5. Swagger UI exposed — `backend/app/main.py`**
FastAPI serves `/docs` and `/redoc` by default. Disable in production by passing `docs_url=None, redoc_url=None` to the `FastAPI()` constructor when `ENV=production`.

**6. No rate limiting on `/analyze`**
Add `slowapi` rate limiting to `POST /api/v1/analyze` before the real analysis engine ships.

## Git Workflow

### Branch Naming

```
main                  # Production-ready code only
<firstname>-<feature> # e.g., aiden-user-authentication
```

### Workflow

1. Branch from `main`: `git checkout -b <firstname>-<feature>`
2. Commit regularly with meaningful messages
3. Write and run tests before opening a PR
4. Open a pull request; request review from at least one team member
5. Address review comments
6. Merge into `main` after approval

### Commit Message Format (Conventional Commits)

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** `feat` | `fix` | `docs` | `style` | `refactor` | `perf` | `test` | `chore` | `ci`

**Rules:**
- Subject line ≤ 50 characters, capitalized, no trailing period
- Use present tense ("add feature" not "added feature")
- Body explains *what* and *why*, not *how*
- Reference issues in footer (e.g., `Closes #123`)

**Examples:**

```
feat(auth): add user login functionality
fix(api): resolve data fetching timeout issue
docs(readme): update installation instructions
test(services): add unit tests for analysis pipeline
```

---

## Development Setup (When Implemented)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Fill in env variables
uvicorn app.main:app --reload   # Runs on http://localhost:8000

# Frontend
cd frontend
npm install
cp .env.example .env
npm start                       # Runs on http://localhost:3000
```

- Backend API docs: http://localhost:8000/docs
- Create `.env` files from `.env.example` templates — never commit `.env`

---

## Key Architectural Decisions

- **Layered backend:** routes → services → models. Keep routes thin.
- **Analysis pipeline:** Submissions go through a multi-stage engine (static analysis + ML). See `docs/CodePulse Engine Pipeline Flowchart.png`.
- **UUID primary keys** everywhere in the database for distributed-system readiness.
- **One-to-one** submission → analysis_report and finding → actionable_fix (a finding has at most one suggested fix).
- **Severity levels** for findings are strictly `'Low'`, `'Med'`, or `'High'` — enforced by DB constraint.
- **Tags** on `actionable_fixes` is a PostgreSQL `TEXT[]` array for flexible categorization.

---

## Project Status

| Area                  | Status      |
|-----------------------|-------------|
| Database schema       | Done |
| Architecture docs     | Done |
| Coding standards      | Done |
| `.env.example` files  | Done |
| `requirements.txt`    | Done |
| `package.json`        | Done |
| CI/CD pipelines       | Done |
| Frontend auth flow    | Done |
| Backend API gateway (FastAPI scaffold, JWT auth, mock `/analyze`, Dockerfile) | Done |
| Frontend — code editor & analysis UI | Done |
| Frontend — dashboard UI redesign (3-col layout, sidebar, dark mode, sparkle btn, profile dropdown) | Done |
| Frontend — unit test suite (CodeEditor, ResultsPanel, ProtectedRoute, AuthContext, LoginPage) | Done (19 tests, all passing) |
| Backend — analysis engine (`engine/`) | Not started |
| Backend — submission persistence | Not started |

---

## Team

- **Aiden Cary** — Team Lead / Developer
- **Keller Willhite** — UI/UX Developer
- **Zachery Atchley** — Integration & Unit Testing / Developer

---

## Frontend UI Architecture (Dashboard)

The dashboard uses a 3-column layout: collapsible submissions sidebar | Monaco editor | results panel.

### Design Tokens (`dashboard.css`)
- Dark mode is the default; light mode toggled via `data-theme="light"` on `<html>`
- Theme stored in `localStorage` key `cp-theme`; applied in a `useEffect` in `DashboardPage`
- Colors defined as CSS vars in `:root` (dark) and `:root[data-theme="light"]` (light overrides)
- Navbar: deep purple gradient (`#9333ea` → `#6e2ebb`); brand/username always `#ffffff`
- No blue anywhere in the palette

### Key Components
| Component | Notes |
|-----------|-------|
| `DashboardPage` | Owns all state: `code`, `results`, `loading`, `error`, `activeId`, `sidebarOpen`, `theme` |
| `SubmissionSidebar` | `forwardRef`; exposes `refresh()` via `useImperativeHandle`; collapses to 52 px mini-bar |
| `CodeEditor` | Controlled (receives `code`/`onCodeChange`); sparkle particle button with CSS animation |
| `ProfileDropdown` | Hash-based avatar color from user ID; closes on outside click |

### Sidebar Collapse Behavior
- `open=true` → full 240 px sidebar; logo resets dashboard, close-icon button on the right collapses it
- `open=false` → 52 px mini-bar; logo crossfades to sidebar-open icon on hover; `+` button opens new submission

### Theme Toggle
- Moon icon shown in dark mode; sun icon shown in light mode
- Button background: `#020202` (dark mode) / `#ffffff` (light mode)

---

## Notes for AI Assistants

- **Keep documentation current.** After completing any feature or story, update `frontend/README.md`, `backend/README.md`, and the relevant sections of this file to reflect what has been built. The Implementation Status tables in each README must stay accurate.
- The project is in **early development**. Most `src/` and `app/` directories do not exist yet — create them when implementing features.
- Always follow the conventions in this file and in `STANDARDS.md`. When in doubt, `STANDARDS.md` is the authoritative reference.
- When creating **backend** files, follow the layered structure: add route handlers to `routes/`, business logic to `services/`, and shared helpers to `utils/`.
- When creating **frontend** files, put components in `components/` (or `pages/` for page-level views) and API call logic in `services/`.
- **Never hardcode** credentials, ports, or environment-specific values — use environment variables and `.env` files.
- The database schema in `backend/database/schema.sql` is the **source of truth**. Align all models with it.
- Write tests alongside new code in `backend/tests/` (Python) and the appropriate `__tests__` directories (JavaScript).
