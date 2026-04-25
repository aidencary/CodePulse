# CodePulse Backend — Requirements

This document defines every functional and non-functional requirement implemented in the
CodePulse FastAPI backend. Each requirement has a unique ID, description, and the source
file(s) where it is implemented. Requirement IDs are referenced by test cases in
[TESTING.md](../TESTING.md) (pattern `TC-{MODULE}-{NNN}`) and by inline comments in
source code (e.g., `# FR-AUTH-007`).

---

## ID Scheme

| Prefix | Module |
|--------|--------|
| `FR-DASH-NNN` | Dashboard / UI shell (backend support) |
| `FR-AUTH-NNN` | Authentication & security |
| `FR-ANALYSIS-NNN` | Code analysis (static + AI) |
| `FR-REPORT-NNN` | Results reporting |
| `FR-ACCT-NNN` | Account management |
| `FR-HIST-NNN` | Submission history |
| `NFR-PERF-NNN` | Performance |
| `NFR-SEC-NNN` | Security / confidentiality |
| `NFR-RELI-NNN` | Reliability |

---

## Functional Requirements

### FR-AUTH — Authentication & Security

| ID | Description | File(s) |
|----|-------------|---------|
| FR-AUTH-007 | JWT authentication guard on every protected API route; validates Supabase JWT signature (HS256 and ES256), issuer, audience, and expiry; extracts `sub` claim as user ID; returns 401 on any validation failure | `app/dependencies.py` |
| FR-AUTH-008 | Code encryption at rest (Not Implemented — confidentiality enforced by RLS and JWT instead; see [docs/REQUIREMENTS.md](../docs/REQUIREMENTS.md) for deviation details) | — |

### FR-ANALYSIS — Code Analysis

| ID | Description | File(s) |
|----|-------------|---------|
| FR-ANALYSIS-001 | Python AST parsing using the built-in `ast` module; syntax error detection returns High-severity finding with error message and line number | `app/services/engines/python_engine.py` |
| FR-ANALYSIS-002 | 48 PEP 8 / AST-based static checks covering: naming conventions (function, class, variable, self/cls, ambiguous names, exception naming, dunder validation, module naming), code style (long lines, trailing whitespace, tab indentation, blank line spacing, semicolons, compound statements, bracket/punctuation/operator/keyword-arg/binary-operator/arrow/annotation whitespace), imports (multi-import, import ordering, relative imports), documentation (missing docstrings, triple-quote style, comment spacing/capitalization/indentation, quote consistency), and best practices (None/boolean/type comparisons, empty sequence checks, lambda assignment, is-not preference, return consistency, BaseException inheritance, string prefix slicing, broad try blocks, context manager usage, is True/False, return in finally, implicit return None, module dunder placement) | `app/services/engines/python_engine.py` |
| FR-ANALYSIS-003 | AI-assisted bug prediction using OpenAI GPT-4o-mini via Chat Completions API; structured prompt includes static findings to avoid duplication; temperature=0 and seed=42 for deterministic output; max 10 bugs returned; graceful fallback to empty list on API error, malformed JSON, or schema validation failure | `app/services/gpt_predictor.py`, `app/services/prompts/python_prompt.py` |
| FR-ANALYSIS-004 | GPT-generated descriptive submission names (2-5 words) for new submissions when user does not provide one; temperature=0.3, max 20 tokens; fallback to "Untitled Submission" | `app/services/gpt_predictor.py` |
| FR-ANALYSIS-005 | Reanalysis of an existing submission: verifies ownership, preserves original name, deletes old analysis results, updates code, re-runs full pipeline, and persists new results | `app/services/persistence_service.py`, `app/routes/analysis.py` |
| FR-ANALYSIS-006 | CodeBERT confidence validation: fine-tuned binary classifier (`aidencary/codepulse-codebert`) scores each GPT-predicted bug with P(buggy); bugs below configurable threshold are flagged; flagged bugs skip score penalty; snippet extraction with configurable context window; inline comment stripping to prevent label leakage; sigmoid-based confidence contrast remapping; LRU snippet cache (max 512); non-blocking via `asyncio.to_thread`; safe fallback if model fails to load | `app/services/codebert_validator.py` |

### FR-REPORT — Results Reporting

| ID | Description | File(s) |
|----|-------------|---------|
| FR-REPORT-001 | Quality score computation (0-100): severity penalties for static findings (High=10, Med=5, Low=2) and predicted bugs (critical=8, high=4, medium=2, low=1); flagged bugs skipped; floor at 0 | `app/services/engines/python_engine.py` |
| FR-REPORT-002 | Structured analysis response: `AnalyzeResponse` with `overall_score`, `summary`, `findings` (list of `Finding` with issue_type, line_number, column_start, column_end, severity, message), `predicted_bugs` (list of `PredictedBug` with line_number, bug_type, severity, description, suggested_fix, confidence, flagged), `submission_id`, and `name` | `app/models/analysis.py`, `app/routes/analysis.py` |

### FR-ACCT — Account Management

| ID | Description | File(s) |
|----|-------------|---------|
| FR-ACCT-001 | View and update profile: `GET /api/v1/account/profile` returns email, username, role, profile picture, and created_at; `PATCH /api/v1/account/profile` updates username (unique, 3-20 chars, `^[a-zA-Z0-9_-]+$`) and/or profile picture (HTTPS URL only); 409 on duplicate username; updates both profiles table and auth user_metadata | `app/routes/account.py`, `app/models/account.py` |
| FR-ACCT-002 | Upload profile avatar: `POST /api/v1/account/avatar` accepts multipart file (image/png, image/jpeg, image/webp; max 2 MB); uploads to Supabase Storage bucket `avatars/{user_id}/avatar.{ext}`; updates profile and auth user_metadata with public URL | `app/routes/account.py` |
| FR-ACCT-003 | Change password: `POST /api/v1/account/change-password` verifies current password via Supabase sign-in attempt; updates password via admin API; new password 8-128 chars; 401 if current password wrong | `app/routes/account.py`, `app/models/account.py` |
| FR-ACCT-004 | Delete account: `DELETE /api/v1/account` calls Supabase `auth.admin.delete_user()`; cascades delete of all user data (submissions, reports, findings, bugs) via database FK constraints | `app/routes/account.py` |
| FR-ACCT-005 | Invite user by email: `POST /api/v1/account/invite` calls Supabase `auth.admin.invite_user_by_email()` with redirect to `SITE_URL`; 400 on Supabase error | `app/routes/account.py`, `app/models/account.py` |
| FR-ACCT-006 | Data export (GDPR/CCPA): `GET /api/v1/account/export` returns all user data as `DataExportResponse` — profile + submissions with nested analysis_reports, findings, and predicted_bugs | `app/routes/account.py`, `app/models/account.py` |

### FR-HIST — Submission History

| ID | Description | File(s) |
|----|-------------|---------|
| FR-HIST-001 | List submissions: `GET /api/v1/submissions` returns user's submissions with id, name, created_at, overall_score, and pinned_at; sorted pinned-first (by pinned_at desc), then by created_at desc | `app/routes/submissions.py`, `app/services/persistence_service.py` |
| FR-HIST-003 | Rename submission: `PATCH /api/v1/submissions/{id}` updates name (1-100 chars); verifies ownership (403 if not owner); 404 if not found | `app/routes/submissions.py` |
| FR-HIST-004 | Delete submission: `DELETE /api/v1/submissions/{id}` removes submission and cascades deletion of related reports, findings, and bugs; verifies ownership (403 if not owner); 404 if not found | `app/routes/submissions.py` |
| FR-HIST-005 | Pin/unpin submission: `PATCH /api/v1/submissions/{id}/pin` toggles `pinned_at` between current timestamp and NULL; verifies ownership (403 if not owner); 404 if not found | `app/routes/submissions.py` |

### FR-DASH — Dashboard Support

| ID | Description | File(s) |
|----|-------------|---------|
| FR-DASH-005 | Backend support for user invites (delegated to FR-ACCT-005) | `app/routes/account.py` |

---

## Non-Functional Requirements

| ID | Category | Description | File(s) |
|----|----------|-------------|---------|
| NFR-PERF-001 | Efficiency | Analysis results delivered within 5 seconds of submission; static analysis is synchronous, GPT and CodeBERT run asynchronously; CodeBERT uses `asyncio.to_thread` for non-blocking inference | `app/routes/analysis.py`, `app/services/codebert_validator.py` |
| NFR-SEC-001 | Confidentiality | Supabase Row Level Security on all tables ensures users can only access their own data; ownership verification on all submission CRUD operations (403 on violation); service role key used only for server-side writes | `app/routes/submissions.py`, `app/services/persistence_service.py`, `app/dependencies.py`, `database/schema.sql` |
| NFR-SEC-002 | Confidentiality | Passwords stored as bcrypt hashes managed by Supabase Auth; never stored in application database | `app/dependencies.py` (JWT-only, no password handling) |
| NFR-SEC-003 | Input Validation | All API input validated via Pydantic models at API boundary; code max length 100,000 chars; username regex enforced; HTTPS-only profile picture URLs; avatar MIME type and size checks | `app/models/analysis.py`, `app/models/account.py`, `app/routes/account.py` |
| NFR-SEC-004 | Security Headers | Middleware adds `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin` to all responses | `app/main.py` |
| NFR-SEC-005 | CORS | CORS restricted to explicit origins (`ALLOWED_ORIGINS` env var), explicit methods (GET, POST, PUT, PATCH, DELETE, OPTIONS), and explicit headers (Authorization, Content-Type) | `app/main.py` |
| NFR-SEC-006 | API Documentation | Swagger UI and ReDoc disabled in production (`docs_url=None`, `redoc_url=None` unless `DEBUG=true`) | `app/main.py` |
| NFR-RELI-001 | Reliability | System handles submissions up to 100,000 characters without degradation; GPT failures return static results (empty bug list) rather than error; persistence failures are non-fatal (logged, analysis still returned to user); CodeBERT load failure degrades gracefully (returns predictions without confidence scores) | `app/routes/analysis.py`, `app/services/gpt_predictor.py`, `app/services/codebert_validator.py` |
| NFR-RELI-002 | Caching | Supabase client cached as singleton (LRU maxsize=1); Settings cached (LRU maxsize=1); JWKS keys cached (LRU maxsize=4); CodeBERT snippet scores cached (LRU max 512); CodeBERT model loaded once at startup | `app/database.py`, `app/config.py`, `app/dependencies.py`, `app/services/codebert_validator.py` |

### Not Implemented

| ID | Category | Description |
|----|----------|-------------|
| NFR-SEC-007 | Rate Limiting | `/analyze` endpoint rate limiting via `slowapi` (10 req/min per bearer token, 429 on exceed) — descoped; no `app/limiter.py` exists |

---

## Database Requirements

These requirements are implemented in `database/schema.sql` and enforced at the PostgreSQL level.

| ID | Description | File(s) |
|----|-------------|---------|
| DB-001 | All primary keys are UUIDs (`gen_random_uuid()`) for distributed-system readiness | `database/schema.sql` |
| DB-002 | CASCADE deletes on all foreign keys: deleting a user cascades to submissions, reports, findings, fixes, and bugs | `database/schema.sql` |
| DB-003 | One-to-one relationship: `submissions` to `analysis_reports` (UNIQUE FK), `findings` to `actionable_fixes` (UNIQUE FK) | `database/schema.sql` |
| DB-004 | Finding severity constrained to `'Low'`, `'Med'`, `'High'` via CHECK constraint | `database/schema.sql` |
| DB-005 | Predicted bug severity constrained to `'low'`, `'medium'`, `'high'`, `'critical'` via CHECK constraint | `database/schema.sql` |
| DB-006 | Overall score constrained to 0-100 via CHECK constraint | `database/schema.sql` |
| DB-007 | CodeBERT confidence constrained to 0.000-1.000 (NUMERIC(4,3)) with nullable default; flagged boolean defaults to FALSE | `database/schema.sql` |
| DB-008 | Auto-create profile on signup via database trigger (`on_auth_user_created`); username from `raw_user_meta_data` or email prefix | `database/schema.sql` |
| DB-009 | RLS policies on all tables: profiles, submissions, analysis_reports, findings, actionable_fixes, predicted_bugs; ownership chains for nested tables | `database/schema.sql` |
| DB-010 | Supabase Storage `avatars` bucket: 2 MB file size limit, PNG/JPEG/WebP MIME types, public read, authenticated upload/update/delete scoped to own folder | `database/schema.sql` |
| DB-011 | Submission pinning: `pinned_at` timestamp column (nullable) on `submissions` table for sort ordering | `database/schema.sql` |

---

## Test Coverage

206 backend tests across 8 test files. See [TESTING.md](../TESTING.md) for the full
test matrix mapping `TC-{MODULE}-{NNN}` IDs to requirements.

| Test File | Tests | Requirements Covered |
|-----------|-------|---------------------|
| `test_analysis_engine.py` | 130 | FR-ANALYSIS-001, FR-ANALYSIS-002, FR-REPORT-001 |
| `test_codebert_validator.py` | 23 | FR-ANALYSIS-006 |
| `test_gpt_predictor.py` | 8 | FR-ANALYSIS-003, FR-ANALYSIS-004, NFR-RELI-001 |
| `test_analyze_endpoint.py` | 6 | FR-ANALYSIS-001, FR-AUTH-007 |
| `test_analyze_route.py` | 7 | FR-REPORT-001, FR-REPORT-002, NFR-PERF-001, NFR-RELI-001 |
| `test_account_routes.py` | 18 | FR-ACCT-001 through FR-ACCT-006, FR-AUTH-007 |
| `test_submission_routes.py` | 13 | FR-HIST-001, FR-HIST-003 through FR-HIST-005, FR-AUTH-007, NFR-SEC-001 |
| `test_placeholder.py` | 1 | — |
