# CodePulse — Testing & CI/CD Guide

This document explains how testing is structured, how to run tests locally, and how the CI/CD pipeline works.

---

## Overview

| Layer | Framework | Runner |
|-------|-----------|--------|
| Frontend | React Testing Library + Jest | `npm test` |
| Backend | pytest | `pytest` |
| API Integration | Postman / Newman | `newman run` |
| CI/CD | GitHub Actions | Runs on every push / PR to `main` |

---

## Frontend Testing

### Setup

Testing libraries are bundled with the project via Create React App. No additional installation is required beyond `npm install`.

`src/setupTests.js` runs before every test suite and imports `@testing-library/jest-dom`, which adds DOM-specific matchers like `.toBeInTheDocument()`.

### Running Tests Locally

```bash
cd frontend

# Watch mode (re-runs on file save — use during development)
npm test

# Run once and exit (use before committing)
npm test -- --watchAll=false
```

### Test Files

All test files live in `__tests__/` directories next to the code they test.

| File | What It Tests |
|------|--------------|
| `src/components/__tests__/ProtectedRoute.test.js` | Loading state, unauthenticated redirect to `/login`, authenticated render of children |
| `src/components/__tests__/CodeEditor.test.js` | Renders editor, button click fires onRun, disabled during loading |
| `src/components/__tests__/ResultsPanel.test.js` | Idle, loading, error, score, findings, predicted bugs (expand/collapse), empty states |
| `src/context/__tests__/AuthContext.test.js` | `onAuthStateChange` lifecycle and cleanup, `signIn` / `signUp` / `signOut` call correct Supabase methods with correct arguments |
| `src/pages/__tests__/LoginPage.test.js` | Log In / Sign Up form toggle, form submission handlers, error message display |
| `src/pages/__tests__/AccountPage.test.js` | Profile load/display, username validation, update profile, change password validation/success, delete modal and confirmation (10 tests) |
| `src/components/__tests__/SubmissionSidebar.test.js` | Render names, fallback to code, search filter, rename (double-click/Enter/Escape), delete confirmation, collapsed state (9 tests) |

### Mocking Strategy

Supabase is mocked at the module level in every test file — no real network calls are made. This keeps tests fast, deterministic, and runnable without a live Supabase project.

```js
jest.mock('../../services/supabaseClient', () => ({
  auth: {
    onAuthStateChange: jest.fn(),
    signInWithPassword: jest.fn(),
    signUp: jest.fn(),
    signOut: jest.fn(),
  },
}))
```

### Writing New Frontend Tests

1. Create a `__tests__/` directory next to the component or module you are testing
2. Name the file `<ComponentName>.test.js`
3. Mock any external dependencies (Supabase, `react-router-dom` hooks) at the top of the file
4. Use `render`, `screen`, `fireEvent`, and `waitFor` from `@testing-library/react`
5. Prefer querying by accessible role or label (`getByRole`, `getByLabelText`) over class names or test IDs

---

## Backend Testing

### Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running Tests Locally

```bash
cd backend

# Run all tests with verbose output
pytest tests/ -v

# Run a specific file
pytest tests/test_placeholder.py -v
```

### Test Files

All test files live in `backend/tests/` and follow the `test_<module>.py` naming convention.

| File | What It Tests |
|------|--------------|
| `tests/test_analyze_endpoint.py` | Health check, auth guard (missing header, malformed token, wrong Bearer prefix), valid JWT happy path, request body validation (6 tests) |
| `tests/test_analyze_route.py` | Route integration tests — full response shape, score range, finding/bug schema, persistence failure resilience, max-length validation (6 tests) |
| `tests/test_analysis_engine.py` | Static analyzer — 24 PEP 8 checks (naming conventions, self/cls, None/boolean/type comparisons, empty sequences, lambda assignment, import formatting, is-not preference, return consistency, exception inheritance, string slicing, trailing whitespace, tab indentation, blank line spacing, comment spacing, triple quote style, import ordering, try block scope, context manager usage), syntax errors, score computation (69 tests) |
| `tests/test_gpt_predictor.py` | GPT predictor — valid responses, empty arrays, API errors, malformed JSON, schema validation, prompt construction (6 tests) |
| `tests/test_account_routes.py` | Account CRUD — get profile, update username, duplicate username 409, invalid chars 422, change password (success/wrong/short), avatar upload (success/invalid type), delete account (13 tests) |
| `tests/test_submission_routes.py` | Submission CRUD — list submissions, rename (success/not-found/not-owner/empty-name), delete (success/not-found/not-owner) (9 tests) |
| `tests/test_placeholder.py` | Confirms the test runner is configured correctly |

### Writing New Backend Tests

Follow these conventions:
- One test file per service module (`app/services/foo.py` → `tests/test_foo.py`)
- Use `pytest` fixtures for shared setup (database mocks, test clients)
- Mock all external calls (Supabase, OpenAI) — tests must run without live services
- Follow the Arrange / Act / Assert pattern

### Code Style Requirements

Before pushing backend code, ensure it passes both checks:

```bash
# Auto-format (run this to fix formatting)
black .

# Check formatting without modifying files (what CI runs)
black --check .

# Lint (config in backend/.flake8 — max-line-length=88 to match black)
flake8 .
```

---

## API Integration Testing (Postman / Newman)

A Postman collection at `postman/collections/codepulse-api.postman_collection.json` provides end-to-end API tests using real HTTP requests against a running backend.

### Collection Structure

| Folder | Tests | Auth Required | Description |
|--------|-------|---------------|-------------|
| Health Check | 1 | No | `GET /` — status, response time, content-type |
| Auth Errors | 4 | No | Missing header, no Bearer prefix, invalid JWT, expired JWT |
| Validation Errors | 4 | Yes | Missing code field, wrong type, max length exceeded, empty body |
| Happy Path | 5 | Yes | Valid code, empty string, syntax errors, unicode, non-Python code |
| Account CRUD | 9 | Yes | Get profile, update username, invalid username, wrong/short password, invalid avatar type, no-auth guards |
| Submission CRUD | 8 | Yes | Analyze with/without name, list, rename, rename not-found, delete, delete not-found, list no-auth |

Every response is also checked for security headers (`X-Content-Type-Options`, `X-Frame-Options`) via a collection-level test script.

### Auto-Generated JWT for Local Testing

The collection includes a pre-request script that auto-generates a valid HS256 JWT when `auth_token` is empty. It uses the `jwt_secret` and `supabase_url` variables from the environment file to sign the token. This means you can run the Health Check, Auth Errors, and Validation Errors folders locally without manually providing a token — just start the backend with matching placeholder env vars.

**Important:** The backend must be started **without** a `.env` file (or with env vars matching the CI environment) so the JWT secret matches:

```bash
cd backend
mv .env .env.bak   # temporarily hide real credentials
SUPABASE_URL=https://placeholder.supabase.co \
SUPABASE_ANON_KEY=placeholder-anon-key \
SUPABASE_SERVICE_ROLE_KEY=placeholder-service-role-key \
SUPABASE_JWT_SECRET=ci-test-jwt-secret-at-least-32-chars-long \
OPENAI_API_KEY=placeholder-openai-key \
ALLOWED_ORIGINS='*' \
uvicorn app.main:app --reload
# After testing: mv .env.bak .env
```

### Running Locally with Newman

```bash
# Install Newman
npm install -g newman

# Run Health Check, Auth Errors, and Validation Errors (auto-generates JWT)
newman run postman/collections/codepulse-api.postman_collection.json \
  --environment postman/environments/ci.postman_environment.json \
  --folder "Health Check" --folder "Auth Errors" --folder "Validation Errors"

# Run a specific folder
newman run postman/collections/codepulse-api.postman_collection.json \
  --environment postman/environments/ci.postman_environment.json \
  --folder "Health Check"

# Run with a manually provided token (e.g., a real Supabase JWT)
newman run postman/collections/codepulse-api.postman_collection.json \
  --environment postman/environments/ci.postman_environment.json \
  --env-var "auth_token=YOUR_JWT_HERE"
```

### Environment Variables

The CI environment (`postman/environments/ci.postman_environment.json`) provides:

| Variable | Purpose |
|----------|---------|
| `base_url` | Backend URL (default: `http://localhost:8000`) |
| `auth_token` | JWT for authenticated requests (auto-generated if empty) |
| `jwt_secret` | Secret used to sign auto-generated JWTs (must match backend's `SUPABASE_JWT_SECRET`) |
| `supabase_url` | Supabase project URL used in JWT `iss` claim (must match backend's `SUPABASE_URL`) |
| `expired_token` | Pre-built expired JWT for the "Expired JWT" auth error test |

### Importing into Postman

The collection auto-registers in Postman's Local View if you have the workspace linked (see `.postman/resources.yaml`). Otherwise, import `postman/collections/codepulse-api.postman_collection.json` manually.

---

## CI/CD — GitHub Actions

Three workflows run automatically. They are path-filtered so only the relevant workflow triggers when files change.

### Frontend CI

**File:** `.github/workflows/frontend-ci.yml`
**Triggers:** Push or PR to `main` where `frontend/**` files changed

| Step | Command | Notes |
|------|---------|-------|
| Install | `npm ci` | Clean install from `package-lock.json` |
| Audit | `npm audit --audit-level=critical` | Fails only on critical vulnerabilities; high-severity false positives from `react-scripts` transitive deps are excluded by design |
| Test | `npm test -- --watchAll=false --ci` | Fails the build if any test fails |
| Build | `npm run build` | Verifies the production build compiles |

The test step uses placeholder Supabase values — all Supabase calls are mocked in tests so no real credentials are needed. The build step uses real values from GitHub Secrets.

**Required GitHub Secrets** (Settings → Secrets → Actions):

| Secret | Used In |
|--------|---------|
| `REACT_APP_SUPABASE_URL` | Build step |
| `REACT_APP_SUPABASE_ANON_KEY` | Build step |

### Backend CI

**File:** `.github/workflows/backend-ci.yml`
**Triggers:** Push or PR to `main` where `backend/**` files changed

| Step | Command | Notes |
|------|---------|-------|
| Install | `pip install -r requirements.txt` | Installs pytest, black, flake8 |
| Format check | `black --check .` | Fails if code is not Black-formatted |
| Lint | `flake8 .` | Fails on PEP 8 violations |
| Test | `pytest tests/ -v` | Fails if any test fails |

### API Tests (Newman)

**File:** `.github/workflows/api-tests.yml`
**Triggers:** Push or PR to `main` where `backend/**` or `postman/**` files changed

| Step | What It Does |
|------|-------------|
| Start backend | Launches uvicorn with placeholder env vars and a known JWT secret |
| Generate auth token | Creates a valid HS256 JWT using `python-jose` for the validation tests |
| Health Check folder | Verifies `GET /` returns `200 OK` |
| Auth Errors folder | Tests missing/invalid/expired tokens (no real services needed) |
| Validation Errors folder | Tests bad request bodies with a valid CI token (no real services needed) |
| Happy Path folder | **Only runs** if the repo variable `RUN_HAPPY_PATH` is set to `true` (requires live OpenAI + Supabase) |

The first three folders use placeholder env vars — they never reach OpenAI or Supabase, so no secrets are required for CI.

### Pull Request Rules

A PR to `main` cannot be merged if any CI step fails. Before opening a PR:

1. Run `npm test -- --watchAll=false` (frontend) and/or `pytest tests/ -v` (backend) locally
2. Ensure all tests pass
3. Ensure backend code is Black-formatted (`black .`) and passes `flake8 .`
4. Run `npm audit --audit-level=critical` in `frontend/` — fix anything reported
5. Commit and push — GitHub Actions will run automatically
6. Check the Actions tab on GitHub to confirm all checks are green

---

## Quick Reference

```bash
# Frontend — audit and run tests once
cd frontend && npm audit --audit-level=critical && npm test -- --watchAll=false

# Backend — format, lint, and test
cd backend && black . && flake8 . && pytest tests/ -v

# API integration tests (requires running backend)
newman run postman/collections/codepulse-api.postman_collection.json \
  --environment postman/environments/ci.postman_environment.json \
  --folder "Health Check"
```
