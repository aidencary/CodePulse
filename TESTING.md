# CodePulse — Testing & CI/CD Guide

This document explains how testing is structured, how to run tests locally, and how the CI/CD pipeline works.

---

## Overview

| Layer | Framework | Runner |
|-------|-----------|--------|
| Frontend | React Testing Library + Jest | `npm test` |
| Backend | pytest | `pytest` |
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
| `tests/test_placeholder.py` | Confirms the test runner is configured correctly — replace with real tests as services are implemented |

### Writing New Backend Tests

As each service module is added to `backend/app/services/`, create a corresponding test file:

```
app/services/submission_service.py  →  tests/test_submission_service.py
app/services/analysis_service.py    →  tests/test_analysis_service.py
```

Follow these conventions:
- One test file per service module
- Use `pytest` fixtures for shared setup (database mocks, test clients)
- Mock all external calls (Supabase, ML models) — tests must run without a live database
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

## CI/CD — GitHub Actions

Two workflows run automatically. They are path-filtered so only the relevant workflow triggers when files change.

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
```
