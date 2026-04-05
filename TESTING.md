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
| `src/components/__tests__/SubmissionSidebar.test.js` | Render names, fallback to code, search filter, rename (kebab menu/Enter/Escape), delete confirmation, pin/star toggle, pinned icon display, collapsed state (11 tests) |
| `src/components/__tests__/InviteModal.test.js` | Email invite modal — render, empty-email disable, submit handler, success toast, error display, cancel, backdrop click, loading state (9 tests) |
| `src/components/__tests__/TwoFactorSection.test.js` | TOTP enrollment (enroll call, QR code, manual secret), verification (challengeAndVerify, error), successful enable, unenrollment, status display (11 tests) |
| `src/pages/__tests__/ResetPasswordPage.test.js` | PASSWORD_RECOVERY wait state, form render, password mismatch / too-short validation, successful updateUser, success toast + redirect, expired-link error, button disable while submitting (8 tests) |

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
| `tests/test_analysis_engine.py` | Static analyzer — 46 PEP 8 checks (naming conventions, self/cls, None/boolean/type comparisons, empty sequences, lambda assignment, import formatting, is-not preference, return consistency, exception inheritance, string slicing, trailing whitespace, tab indentation, blank line spacing, comment spacing, triple quote style, import ordering, try block scope, context manager usage, is true/false, exception naming, invalid dunders, return in finally, implicit return none, module dunder placement, relative imports, semicolons, compound statements, bracket whitespace, whitespace before punctuation, whitespace before call, whitespace after separator, operator spacing, keyword arg spacing, binary operator line break, arrow spacing, annotation spacing, block comment capitalization/indentation, quote consistency, module naming), syntax errors, score computation (113 tests) |
| `tests/test_gpt_predictor.py` | GPT predictor — valid responses, empty arrays, API errors, malformed JSON, schema validation, prompt construction, user message formatting (8 tests) |
| `tests/test_account_routes.py` | Account CRUD — get profile, update username, duplicate username 409, invalid chars 422, change password (success/wrong/short), avatar upload (success/invalid type), delete account, invite user (success/supabase error/no auth) (16 tests) |
| `tests/test_submission_routes.py` | Submission CRUD — list submissions, rename (success/not-found/not-owner/empty-name), delete (success/not-found/not-owner), pin toggle (pin/unpin/not-found/not-owner) (13 tests) |
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
| Submission CRUD | 10 | Yes | Analyze with/without name, list, rename, rename not-found, delete, delete not-found, pin, pin not-found, list no-auth |

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

## Test Matrix

Every automated test case is listed here with its ID and the requirement(s) it covers.
Test IDs follow the pattern `TC-{MODULE}-{NNN}`. For full requirement descriptions see
[REQUIREMENTS.md](REQUIREMENTS.md).

---

### Backend — Unit Tests

#### `tests/test_analysis_engine.py`

| TC-ID | Test Function | Requirements Covered |
|-------|---------------|----------------------|
| TC-ANALYSIS-001 | `test_long_line_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-002 | `test_long_line_not_flagged_at_exactly_88` | FR-ANALYSIS-002 |
| TC-ANALYSIS-003 | `test_long_line_not_flagged_below_limit` | FR-ANALYSIS-002 |
| TC-ANALYSIS-004 | `test_missing_docstring_on_function` | FR-ANALYSIS-002 |
| TC-ANALYSIS-005 | `test_missing_docstring_not_flagged_when_present` | FR-ANALYSIS-002 |
| TC-ANALYSIS-006 | `test_dunder_method_not_flagged_for_missing_docstring` | FR-ANALYSIS-002 |
| TC-ANALYSIS-007 | `test_missing_docstring_on_class` | FR-ANALYSIS-002 |
| TC-ANALYSIS-008 | `test_bare_except_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-009 | `test_bare_except_not_flagged_with_type` | FR-ANALYSIS-002 |
| TC-ANALYSIS-010 | `test_syntax_error_returns_high_finding` | FR-ANALYSIS-001, FR-ANALYSIS-002 |
| TC-ANALYSIS-011 | `test_score_is_100_for_clean_code` | FR-REPORT-001 |
| TC-ANALYSIS-012 | `test_score_decreases_with_findings` | FR-REPORT-001 |
| TC-ANALYSIS-013 | `test_score_floor_is_zero` | FR-REPORT-001 |
| TC-ANALYSIS-014 | `test_compute_score_includes_predicted_bugs` | FR-REPORT-001, FR-ANALYSIS-003 |
| TC-ANALYSIS-015 | `test_camel_case_function_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-016 | `test_snake_case_function_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-017 | `test_non_pascal_case_class_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-018 | `test_pascal_case_class_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-019 | `test_ambiguous_name_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-020 | `test_ambiguous_name_not_flagged_for_other_singles` | FR-ANALYSIS-002 |
| TC-ANALYSIS-021 | `test_camel_case_variable_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-022 | `test_wrong_self_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-023 | `test_correct_self_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-024 | `test_wrong_cls_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-025 | `test_staticmethod_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-026 | `test_none_equality_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-027 | `test_none_is_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-028 | `test_boolean_comparison_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-029 | `test_boolean_comparison_not_flagged_for_direct_use` | FR-ANALYSIS-002 |
| TC-ANALYSIS-030 | `test_type_comparison_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-031 | `test_isinstance_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-032 | `test_len_equals_zero_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-033 | `test_truthiness_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-034 | `test_lambda_assignment_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-035 | `test_lambda_in_call_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-036 | `test_multi_import_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-037 | `test_separate_imports_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-038 | `test_from_import_multi_names_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-039 | `test_not_is_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-040 | `test_is_not_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-041 | `test_inconsistent_returns_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-042 | `test_consistent_returns_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-043 | `test_base_exception_inheritance_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-044 | `test_exception_inheritance_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-045 | `test_string_prefix_slicing_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-046 | `test_string_suffix_slicing_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-047 | `test_startswith_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-048 | `test_trailing_whitespace_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-049 | `test_no_trailing_whitespace_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-050 | `test_tab_indentation_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-051 | `test_space_indentation_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-052 | `test_missing_blank_lines_before_top_level_def` | FR-ANALYSIS-002 |
| TC-ANALYSIS-053 | `test_correct_blank_lines_before_top_level_def` | FR-ANALYSIS-002 |
| TC-ANALYSIS-054 | `test_missing_blank_line_between_methods` | FR-ANALYSIS-002 |
| TC-ANALYSIS-055 | `test_correct_blank_line_between_methods` | FR-ANALYSIS-002 |
| TC-ANALYSIS-056 | `test_inline_comment_too_close_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-057 | `test_inline_comment_proper_spacing_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-058 | `test_block_comment_not_flagged_as_inline` | FR-ANALYSIS-002 |
| TC-ANALYSIS-059 | `test_comment_missing_space_after_hash` | FR-ANALYSIS-002 |
| TC-ANALYSIS-060 | `test_comment_with_space_after_hash_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-061 | `test_shebang_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-062 | `test_triple_single_quotes_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-063 | `test_triple_double_quotes_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-064 | `test_stdlib_after_third_party_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-065 | `test_properly_grouped_imports_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-066 | `test_broad_try_block_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-067 | `test_narrow_try_block_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-068 | `test_try_finally_close_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-069 | `test_with_statement_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-084 | `test_is_true_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-085 | `test_is_true_false_not_flagged_for_direct_use` | FR-ANALYSIS-002 |
| TC-ANALYSIS-086 | `test_exception_naming_missing_error_suffix` | FR-ANALYSIS-002 |
| TC-ANALYSIS-087 | `test_exception_naming_with_error_suffix_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-088 | `test_invalid_dunder_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-089 | `test_valid_dunder_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-090 | `test_return_in_finally_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-091 | `test_no_return_in_finally_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-092 | `test_implicit_return_none_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-093 | `test_implicit_return_none_not_flagged_for_consistent` | FR-ANALYSIS-002 |
| TC-ANALYSIS-094 | `test_module_dunder_after_import_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-095 | `test_module_dunder_before_import_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-096 | `test_relative_import_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-097 | `test_absolute_import_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-098 | `test_semicolon_statement_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-099 | `test_no_semicolon_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-100 | `test_compound_statement_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-101 | `test_compound_statement_not_flagged_for_multiline` | FR-ANALYSIS-002 |
| TC-ANALYSIS-102 | `test_bracket_whitespace_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-103 | `test_bracket_whitespace_not_flagged_for_clean` | FR-ANALYSIS-002 |
| TC-ANALYSIS-104 | `test_whitespace_before_punctuation_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-105 | `test_whitespace_before_punctuation_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-106 | `test_whitespace_before_call_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-107 | `test_whitespace_before_call_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-108 | `test_whitespace_after_separator_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-109 | `test_whitespace_after_separator_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-110 | `test_operator_spacing_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-111 | `test_operator_spacing_not_flagged_for_spaced` | FR-ANALYSIS-002 |
| TC-ANALYSIS-112 | `test_keyword_arg_spacing_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-113 | `test_keyword_arg_spacing_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-114 | `test_binary_operator_line_break_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-115 | `test_binary_operator_line_break_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-116 | `test_arrow_spacing_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-117 | `test_arrow_spacing_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-118 | `test_annotation_spacing_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-119 | `test_annotation_spacing_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-120 | `test_block_comment_capitalization_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-121 | `test_block_comment_capitalization_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-122 | `test_block_comment_indentation_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-123 | `test_block_comment_indentation_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-124 | `test_quote_consistency_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-125 | `test_quote_consistency_not_flagged` | FR-ANALYSIS-002 |
| TC-ANALYSIS-126 | `test_module_naming_detected` | FR-ANALYSIS-002 |
| TC-ANALYSIS-127 | `test_module_naming_not_flagged` | FR-ANALYSIS-002 |

#### `tests/test_gpt_predictor.py`

| TC-ID | Test Function | Requirements Covered |
|-------|---------------|----------------------|
| TC-ANALYSIS-070 | `test_returns_predicted_bugs_on_valid_response` | FR-ANALYSIS-003 |
| TC-ANALYSIS-071 | `test_returns_empty_list_on_empty_predicted_bugs_array` | FR-ANALYSIS-003 |
| TC-ANALYSIS-072 | `test_returns_empty_list_on_api_error` | FR-ANALYSIS-003, NFR-RELI-001 |
| TC-ANALYSIS-073 | `test_returns_empty_list_on_malformed_json` | FR-ANALYSIS-003, NFR-RELI-001 |
| TC-ANALYSIS-074 | `test_returns_empty_list_on_schema_validation_failure` | FR-ANALYSIS-003, NFR-RELI-001 |
| TC-ANALYSIS-075 | `test_system_prompt_includes_static_findings` | FR-ANALYSIS-003 |
| TC-ANALYSIS-076 | `test_user_message_prefixes_each_line_with_line_number` | FR-ANALYSIS-003 |
| TC-ANALYSIS-077 | `test_user_message_preserves_blank_lines` | FR-ANALYSIS-003 |

---

### Backend — Integration Tests

#### `tests/test_analyze_endpoint.py`

| TC-ID | Test Function | Requirements Covered |
|-------|---------------|----------------------|
| TC-AUTH-001 | `test_health_check` | — |
| TC-AUTH-002 | `test_analyze_missing_auth_header` | FR-AUTH-007 |
| TC-AUTH-003 | `test_analyze_malformed_token` | FR-AUTH-007 |
| TC-AUTH-004 | `test_analyze_wrong_prefix` | FR-AUTH-007 |
| TC-ANALYSIS-084 | `test_analyze_valid_token_returns_analysis` | FR-ANALYSIS-001, FR-AUTH-007 |
| TC-ANALYSIS-085 | `test_analyze_missing_code_field` | FR-ANALYSIS-001 |

#### `tests/test_analyze_route.py`

| TC-ID | Test Function | Requirements Covered |
|-------|---------------|----------------------|
| TC-ANALYSIS-078 | `test_analyze_returns_correct_shape` | FR-REPORT-001, FR-REPORT-002 |
| TC-ANALYSIS-079 | `test_analyze_score_in_range` | FR-REPORT-001, NFR-PERF-001 |
| TC-ANALYSIS-080 | `test_analyze_findings_have_required_fields` | FR-REPORT-001 |
| TC-ANALYSIS-081 | `test_analyze_predicted_bugs_have_required_fields` | FR-REPORT-002 |
| TC-ANALYSIS-082 | `test_analyze_persistence_failure_still_returns_200` | NFR-RELI-001 |
| TC-ANALYSIS-083 | `test_analyze_code_too_long_returns_422` | NFR-RELI-001 |

#### `tests/test_account_routes.py`

| TC-ID | Test Function | Requirements Covered |
|-------|---------------|----------------------|
| TC-ACCT-001 | `test_get_profile_success` | FR-ACCT-001 |
| TC-ACCT-002 | `test_get_profile_no_auth` | FR-AUTH-007 |
| TC-ACCT-003 | `test_update_profile_username` | FR-ACCT-001 |
| TC-ACCT-004 | `test_update_profile_duplicate_username` | FR-ACCT-001 |
| TC-ACCT-005 | `test_update_profile_invalid_username_chars` | FR-ACCT-001 |
| TC-ACCT-006 | `test_update_profile_no_fields` | FR-ACCT-001 |
| TC-ACCT-007 | `test_change_password_success` | FR-ACCT-003 |
| TC-ACCT-008 | `test_change_password_wrong_current` | FR-ACCT-003 |
| TC-ACCT-009 | `test_change_password_too_short` | FR-ACCT-003 |
| TC-ACCT-010 | `test_upload_avatar_success` | FR-ACCT-002 |
| TC-ACCT-011 | `test_upload_avatar_invalid_type` | FR-ACCT-002 |
| TC-ACCT-012 | `test_delete_account_success` | FR-ACCT-004 |
| TC-ACCT-013 | `test_delete_account_no_auth` | FR-AUTH-007 |
| TC-ACCT-014 | `test_invite_user_success` | FR-ACCT-005 |
| TC-ACCT-015 | `test_invite_user_supabase_error` | FR-ACCT-005 |
| TC-ACCT-016 | `test_invite_user_no_auth` | FR-AUTH-007 |

#### `tests/test_submission_routes.py`

| TC-ID | Test Function | Requirements Covered |
|-------|---------------|----------------------|
| TC-HIST-001 | `test_list_submissions_success` | FR-HIST-001 |
| TC-HIST-002 | `test_list_submissions_no_auth` | FR-AUTH-007 |
| TC-HIST-003 | `test_rename_submission_success` | FR-HIST-003 |
| TC-HIST-004 | `test_rename_submission_not_found` | FR-HIST-003 |
| TC-HIST-005 | `test_rename_submission_not_owner` | FR-HIST-003, NFR-SEC-001 |
| TC-HIST-006 | `test_rename_submission_empty_name` | FR-HIST-003 |
| TC-HIST-007 | `test_delete_submission_success` | FR-HIST-004 |
| TC-HIST-008 | `test_delete_submission_not_found` | FR-HIST-004 |
| TC-HIST-009 | `test_delete_submission_not_owner` | FR-HIST-004, NFR-SEC-001 |
| TC-HIST-010 | `test_toggle_pin_success` | FR-HIST-005 |
| TC-HIST-011 | `test_toggle_unpin_success` | FR-HIST-005 |
| TC-HIST-012 | `test_toggle_pin_not_found` | FR-HIST-005 |
| TC-HIST-013 | `test_toggle_pin_not_owner` | FR-HIST-005, NFR-SEC-001 |

---

### Frontend — Unit Tests

#### `src/components/__tests__/ProtectedRoute.test.js`

| TC-ID | Test Description | Requirements Covered |
|-------|-----------------|----------------------|
| TC-AUTH-005 | renders loading indicator while auth state is initializing | FR-AUTH-007, NFR-USAB-001 |
| TC-AUTH-006 | redirects to /login when user is not authenticated | FR-AUTH-007 |
| TC-AUTH-007 | renders children when user is authenticated | FR-AUTH-007 |

#### `src/components/__tests__/CodeEditor.test.js`

| TC-ID | Test Description | Requirements Covered |
|-------|-----------------|----------------------|
| TC-DASH-001 | renders the editor and run button | FR-DASH-001 |
| TC-DASH-002 | calls onRun with the current editor content when button is clicked | FR-DASH-001 |
| TC-DASH-003 | disables the run button when loading is true | FR-DASH-002, NFR-USAB-001 |
| TC-DASH-004 | renders the copy button and it is disabled when code is empty | FR-DASH-001 |

#### `src/components/__tests__/ResultsPanel.test.js`

| TC-ID | Test Description | Requirements Covered |
|-------|-----------------|----------------------|
| TC-REPORT-001 | shows idle placeholder when there are no results | FR-REPORT-001 |
| TC-REPORT-002 | shows the error message on failure | FR-REPORT-001, NFR-RELI-001 |
| TC-REPORT-003 | shows the skeleton with aria-label while loading | FR-DASH-002, NFR-USAB-001 |
| TC-REPORT-004 | does not show the skeleton when not loading | FR-DASH-002 |
| TC-REPORT-005 | displays the overall score | FR-REPORT-001 |
| TC-REPORT-006 | displays the summary text | FR-REPORT-001 |
| TC-REPORT-007 | renders each finding type | FR-REPORT-001 |
| TC-REPORT-008 | renders finding line numbers | FR-REPORT-001 |
| TC-REPORT-009 | renders finding messages | FR-REPORT-001 |
| TC-REPORT-010 | shows empty state when findings array is empty | FR-REPORT-001 |
| TC-REPORT-011 | renders the bug type | FR-REPORT-002 |
| TC-REPORT-012 | renders the bug description | FR-REPORT-002 |
| TC-REPORT-013 | renders the bug line number | FR-REPORT-002 |
| TC-REPORT-014 | does not render line number when bug.line_number is null | FR-REPORT-002 |
| TC-REPORT-015 | expands suggested fix when toggle is clicked | FR-REPORT-002 |
| TC-REPORT-016 | collapses suggested fix on second click | FR-REPORT-002 |
| TC-REPORT-017 | shows empty state when predicted_bugs array is empty | FR-REPORT-002 |
| TC-REPORT-018 | ignoring a finding removes it from the list | FR-REPORT-004 |
| TC-REPORT-019 | ignoring a bug removes it from the list | FR-REPORT-004 |
| TC-REPORT-020 | ignored items reappear when results are reset | FR-REPORT-004 |
| TC-REPORT-021 | calls onHoverLine with line number when hovering a finding | FR-REPORT-005, FR-DASH-006 |
| TC-REPORT-022 | calls onHoverLine with null when leaving a finding | FR-REPORT-005, FR-DASH-006 |
| TC-REPORT-023 | calls onHoverLine with line number when hovering a bug card | FR-REPORT-005, FR-DASH-006 |
| TC-REPORT-024 | does not call onHoverLine when bug has no line number | FR-REPORT-005 |
| TC-REPORT-025 | clicking the Line pill re-orders findings by line number ascending | FR-REPORT-003 |
| TC-REPORT-026 | direction toggle reverses line sort to descending | FR-REPORT-003 |
| TC-REPORT-027 | equal-severity findings are tiebroken by line number ascending | FR-REPORT-003 |
| TC-REPORT-028 | null line_number findings sort last when Line sort is active | FR-REPORT-003 |

#### `src/components/__tests__/SubmissionSidebar.test.js`

| TC-ID | Test Description | Requirements Covered |
|-------|-----------------|----------------------|
| TC-HIST-014 | renders submissions with names | FR-HIST-001 |
| TC-HIST-015 | falls back to first code line when name is null | FR-HIST-001 |
| TC-HIST-016 | filters submissions by search input | FR-HIST-006 |
| TC-HIST-017 | shows rename input via kebab menu | FR-HIST-003 |
| TC-HIST-018 | saves rename on Enter key | FR-HIST-003 |
| TC-HIST-019 | does not call renameSubmission when name is unchanged | FR-HIST-003 |
| TC-HIST-020 | cancels rename on Escape key without calling API | FR-HIST-003 |
| TC-HIST-021 | shows centered delete modal via kebab menu | FR-HIST-004 |
| TC-HIST-022 | calls deleteSubmission when delete is confirmed | FR-HIST-004 |
| TC-HIST-023 | renders collapsed mini-bar when open is false | FR-DASH-004 |
| TC-HIST-024 | calls pinSubmission via kebab Star option | FR-HIST-005 |
| TC-HIST-025 | shows pin star icon on pinned submissions | FR-HIST-005 |

#### `src/components/__tests__/InviteModal.test.js`

| TC-ID | Test Description | Requirements Covered |
|-------|-----------------|----------------------|
| TC-ACCT-017 | renders title, hint, email input, and action buttons | FR-ACCT-005, FR-DASH-005 |
| TC-ACCT-018 | disables Send Invite when email is empty | FR-ACCT-005 |
| TC-ACCT-019 | enables Send Invite once an email is entered | FR-ACCT-005 |
| TC-ACCT-020 | calls inviteUser with the token and trimmed email on submit | FR-ACCT-005 |
| TC-ACCT-021 | shows success toast and closes modal on successful invite | FR-ACCT-005 |
| TC-ACCT-022 | displays the error message and does not close on a failed invite | FR-ACCT-005 |
| TC-ACCT-023 | calls onClose when Cancel is clicked | FR-ACCT-005 |
| TC-ACCT-024 | calls onClose when the backdrop is clicked | FR-ACCT-005 |
| TC-ACCT-025 | shows Sending and disables the button while the request is in-flight | FR-ACCT-005 |

#### `src/components/__tests__/TwoFactorSection.test.js`

| TC-ID | Test Description | Requirements Covered |
|-------|-----------------|----------------------|
| TC-AUTH-008 | shows Enable 2FA when no verified factor exists | FR-AUTH-003 |
| TC-AUTH-009 | shows 2FA Enabled and Disable 2FA when a verified factor exists | FR-AUTH-003 |
| TC-AUTH-010 | clicking Enable 2FA calls enroll and shows QR code | FR-AUTH-003 |
| TC-AUTH-011 | QR code img has src matching the returned qr_code URI | FR-AUTH-003 |
| TC-AUTH-012 | displays the manual secret after enrollment | FR-AUTH-003 |
| TC-AUTH-013 | calls challengeAndVerify with correct factorId and trimmed code on Verify | FR-AUTH-004 |
| TC-AUTH-014 | shows error on failed verification | FR-AUTH-004 |
| TC-AUTH-015 | shows 2FA Enabled and removes QR code on successful verification | FR-AUTH-003, FR-AUTH-004 |
| TC-AUTH-016 | calls unenroll with the factorId when Disable 2FA is clicked | FR-AUTH-005 |
| TC-AUTH-017 | shows Enable 2FA again after successful unenroll | FR-AUTH-005 |
| TC-AUTH-018 | shows error on failed unenroll | FR-AUTH-005 |

#### `src/context/__tests__/AuthContext.test.js`

| TC-ID | Test Description | Requirements Covered |
|-------|-----------------|----------------------|
| TC-AUTH-019 | subscribes to onAuthStateChange on mount and unsubscribes on unmount | FR-AUTH-002 |
| TC-AUTH-020 | signIn calls supabase.auth.signInWithPassword with email and password | FR-AUTH-002 |
| TC-AUTH-021 | signUp calls supabase.auth.signUp with email, password, and username metadata | FR-AUTH-001 |
| TC-AUTH-022 | signOut calls supabase.auth.signOut | FR-AUTH-002 |

#### `src/pages/__tests__/LoginPage.test.js`

| TC-ID | Test Description | Requirements Covered |
|-------|-----------------|----------------------|
| TC-AUTH-023 | renders Log In form by default without username field | FR-AUTH-002 |
| TC-AUTH-024 | shows username field after switching to Sign Up mode | FR-AUTH-001 |
| TC-AUTH-025 | calls signIn with email and password on login form submit | FR-AUTH-002 |
| TC-AUTH-026 | calls signUp with email, password, and username on signup form submit | FR-AUTH-001 |
| TC-AUTH-027 | displays error message when signIn returns an error | FR-AUTH-002 |
| TC-AUTH-028 | does not show Forgot password before a failed login attempt | FR-AUTH-006 |
| TC-AUTH-029 | shows Forgot password after a failed login attempt | FR-AUTH-006 |
| TC-AUTH-030 | shows forgot password email form when Forgot password is clicked | FR-AUTH-006 |
| TC-AUTH-031 | calls resetPasswordForEmail with the entered email | FR-AUTH-006 |
| TC-AUTH-032 | shows success message after reset email is sent | FR-AUTH-006 |
| TC-AUTH-033 | shows error message when resetPasswordForEmail fails | FR-AUTH-006 |
| TC-AUTH-034 | returns to login mode when Back to Log In is clicked | FR-AUTH-006 |
| TC-AUTH-035 | shows MFA code input after successful login when AAL step-up is required | FR-AUTH-004 |
| TC-AUTH-036 | does not show MFA step when nextLevel is aal1 | FR-AUTH-004 |
| TC-AUTH-037 | calls challenge and verify with factorId and code on MFA submit | FR-AUTH-004 |
| TC-AUTH-038 | shows Invalid code error on verify failure | FR-AUTH-004 |
| TC-AUTH-039 | signs out and returns to credentials when Back to Log In is clicked in MFA | FR-AUTH-004 |

#### `src/pages/__tests__/AccountPage.test.js`

| TC-ID | Test Description | Requirements Covered |
|-------|-----------------|----------------------|
| TC-ACCT-026 | renders all sections after profile loads | FR-ACCT-001, FR-ACCT-002, FR-ACCT-003, FR-ACCT-004 |
| TC-ACCT-027 | displays profile data in form fields | FR-ACCT-001 |
| TC-ACCT-028 | shows validation error when username is too short | FR-ACCT-001 |
| TC-ACCT-029 | shows validation error when username has invalid characters | FR-ACCT-001 |
| TC-ACCT-030 | calls updateProfile and shows success toast on valid update | FR-ACCT-001 |
| TC-ACCT-031 | shows error when new password and confirm password do not match | FR-ACCT-003 |
| TC-ACCT-032 | shows error when new password is too short | FR-ACCT-003 |
| TC-ACCT-033 | calls changePassword and shows success toast on valid password change | FR-ACCT-003 |
| TC-ACCT-034 | shows delete confirmation modal when Delete Account is clicked | FR-ACCT-004 |
| TC-ACCT-035 | keeps delete button disabled until username matches | FR-ACCT-004 |

#### `src/pages/__tests__/ResetPasswordPage.test.js`

| TC-ID | Test Description | Requirements Covered |
|-------|-----------------|----------------------|
| TC-AUTH-040 | shows loading state while waiting for PASSWORD_RECOVERY event | FR-AUTH-006 |
| TC-AUTH-041 | shows password form once PASSWORD_RECOVERY fires | FR-AUTH-006 |
| TC-AUTH-042 | shows error when passwords do not match | FR-AUTH-006 |
| TC-AUTH-043 | shows error when password is shorter than 8 characters | FR-AUTH-006 |
| TC-AUTH-044 | calls updateUser with the new password on valid submit | FR-AUTH-006 |
| TC-AUTH-045 | calls toast and navigates to /login on success | FR-AUTH-006 |
| TC-AUTH-046 | shows error message when updateUser returns an error (expired link) | FR-AUTH-006 |
| TC-AUTH-047 | disables submit button while submitting | FR-AUTH-006 |

---

### API Integration Tests (Postman / Newman)

| TC-ID | Postman Request Name | Folder | Requirements Covered |
|-------|---------------------|--------|----------------------|
| TC-API-001 | TC-API-001: GET / — 200 OK | Health Check | — |
| TC-API-002 | TC-API-002: No Authorization header — 422 | Auth Errors | FR-AUTH-007 |
| TC-API-003 | TC-API-003: Missing Bearer prefix — 401 | Auth Errors | FR-AUTH-007 |
| TC-API-004 | TC-API-004: Invalid JWT — 401 | Auth Errors | FR-AUTH-007 |
| TC-API-005 | TC-API-005: Expired JWT — 401 | Auth Errors | FR-AUTH-007 |
| TC-API-006 | TC-API-006: Missing code field — 422 | Validation Errors | FR-ANALYSIS-001 |
| TC-API-007 | TC-API-007: Wrong type for code (int) — 422 | Validation Errors | FR-ANALYSIS-001 |
| TC-API-008 | TC-API-008: Code exceeds max length — 422 | Validation Errors | NFR-RELI-001 |
| TC-API-009 | TC-API-009: Empty body — 422 | Validation Errors | FR-ANALYSIS-001 |
| TC-API-010 | TC-API-010: Valid Python code — 200 | Happy Path | FR-ANALYSIS-001, FR-ANALYSIS-002, FR-ANALYSIS-003, FR-REPORT-001, FR-REPORT-002 |
| TC-API-011 | TC-API-011: Empty code string — 200 | Happy Path | FR-ANALYSIS-001 |
| TC-API-012 | TC-API-012: Code with syntax errors — 200 | Happy Path | FR-ANALYSIS-001, FR-REPORT-001 |
| TC-API-013 | TC-API-013: Unicode and special characters — 200 | Happy Path | NFR-RELI-001 |
| TC-API-014 | TC-API-014: Non-Python code — 200 | Happy Path | FR-ANALYSIS-001 |
| TC-API-015 | TC-API-015: Get Profile — 200 | Account CRUD | FR-ACCT-001 |
| TC-API-016 | TC-API-016: Update Username — 200 | Account CRUD | FR-ACCT-001 |
| TC-API-017 | TC-API-017: Update Username — invalid chars — 422 | Account CRUD | FR-ACCT-001 |
| TC-API-018 | TC-API-018: Change Password — wrong current — 401 | Account CRUD | FR-ACCT-003 |
| TC-API-019 | TC-API-019: Change Password — too short — 422 | Account CRUD | FR-ACCT-003 |
| TC-API-020 | TC-API-020: Upload Avatar — invalid type — 422 | Account CRUD | FR-ACCT-002 |
| TC-API-021 | TC-API-021: Get Profile — no auth — 422 | Account CRUD | FR-AUTH-007 |
| TC-API-022 | TC-API-022: Change Password — no auth — 422 | Account CRUD | FR-AUTH-007 |
| TC-API-023 | TC-API-023: Delete Account — no auth — 422 | Account CRUD | FR-AUTH-007 |
| TC-API-024 | TC-API-024: Analyze with custom name — 200 | Submission CRUD | FR-ANALYSIS-001, FR-HIST-001 |
| TC-API-025 | TC-API-025: Analyze without name (GPT generates) — 200 | Submission CRUD | FR-ANALYSIS-004 |
| TC-API-026 | TC-API-026: List submissions — 200 | Submission CRUD | FR-HIST-001 |
| TC-API-027 | TC-API-027: Rename submission — 200 | Submission CRUD | FR-HIST-003 |
| TC-API-028 | TC-API-028: Rename — not found — 404 | Submission CRUD | FR-HIST-003 |
| TC-API-029 | TC-API-029: Delete submission — 200 | Submission CRUD | FR-HIST-004 |
| TC-API-030 | TC-API-030: Delete — not found — 404 | Submission CRUD | FR-HIST-004 |
| TC-API-031 | TC-API-031: Pin submission — 200 | Submission CRUD | FR-HIST-005 |
| TC-API-032 | TC-API-032: Pin — not found — 404 | Submission CRUD | FR-HIST-005 |
| TC-API-033 | TC-API-033: List submissions — no auth — 422 | Submission CRUD | FR-AUTH-007 |

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
