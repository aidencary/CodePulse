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
| `tests/test_analyze_endpoint.py` | Health check, auth guard (missing header, malformed token, wrong Bearer prefix), valid JWT happy path, request body validation |
| `tests/test_analyze_route.py` | Route integration tests — full response shape, score range, finding/bug schema, persistence failure resilience |
| `tests/test_analysis_engine.py` | Static analyzer — 21 PEP 8 checks (naming conventions, self/cls, None/boolean/type comparisons, empty sequences, lambda assignment, import formatting, is-not preference, return consistency, exception inheritance, string slicing, trailing whitespace, tab indentation, blank line spacing, comment spacing, triple quote style), syntax errors, score computation (63 tests) |
| `tests/test_gpt_predictor.py` | GPT predictor — valid responses, empty arrays, API errors, malformed JSON, schema validation, prompt construction |
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

Every response is also checked for security headers (`X-Content-Type-Options`, `X-Frame-Options`) via a collection-level test script.

### Running Locally with Newman

```bash
# Install Newman
npm install -g newman

# Run all folders (requires a running backend and valid auth_token)
newman run postman/collections/codepulse-api.postman_collection.json \
  --environment postman/environments/ci.postman_environment.json \
  --env-var "auth_token=YOUR_JWT_HERE"

# Run a specific folder
newman run postman/collections/codepulse-api.postman_collection.json \
  --environment postman/environments/ci.postman_environment.json \
  --folder "Health Check"
```

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
