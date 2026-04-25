# CodePulse — Requirements

This document defines the machine-readable requirement IDs for CodePulse, derived from the
original Requirements Analysis document (March 3, 2026). Each source-code file and test
that implements a requirement carries a matching inline comment (e.g., `// FR-AUTH-001` or
`# FR-AUTH-001`) so requirements can be located by searching the codebase.

---

## ID Scheme

| Prefix | Module |
|--------|--------|
| `FR-DASH-NNN` | Dashboard / UI shell |
| `FR-AUTH-NNN` | Authentication & security |
| `FR-ANALYSIS-NNN` | Code analysis (static + AI) |
| `FR-REPORT-NNN` | Results reporting & display |
| `FR-ACCT-NNN` | Account management |
| `FR-HIST-NNN` | Submission history |
| `NFR-PERF-NNN` | Performance |
| `NFR-USAB-NNN` | Usability |
| `NFR-SEC-NNN` | Security / confidentiality |
| `NFR-RELI-NNN` | Reliability |

Test-case IDs follow the same module structure: `TC-{MODULE}-{NNN}` (see `TESTING.md`).

---

## Implementation Status Key

| Status | Meaning |
|--------|---------|
| **Implemented** | Feature delivered as specified in the original requirements |
| **Changed** | Requirement delivered but implementation differs from the original specification; deviation documented in the [Requirement Deviations](#requirement-deviations) section |
| **Not Implemented** | Requirement was descoped or deferred |

---

## Functional Requirements

### FR-DASH — Dashboard / UI Shell

| ID | Original REQ-N | Description | Status |
|----|---------------|-------------|--------|
| FR-DASH-001 | REQ-1 | Web dashboard for pasting and submitting source code | Implemented |
| FR-DASH-002 | REQ-14 | Dashboard remains interactive and displays loading state while analysis is in progress | Implemented |
| FR-DASH-003 | — | Dark / light theme toggle with `localStorage` persistence | Implemented |
| FR-DASH-004 | — | Three-column layout: collapsible sidebar / Monaco editor / results panel | Implemented |
| FR-DASH-005 | — | Invite new users by email via in-dashboard modal | Implemented |
| FR-DASH-006 | — | Line-highlight orchestration between results panel and editor on hover | Implemented |
| FR-DASH-007 | — | Click-to-jump: clicking a finding or bug card scrolls the editor to the corresponding line | Implemented |
| FR-DASH-008 | — | Help modal ("?") button in dashboard nav explaining pipeline, scoring, static analysis, AI predictions, and CodeBERT confidence tiers | Implemented |
| FR-DASH-009 | — | Profile dropdown in navbar with hash-based avatar color, links to Account page and Sign Out | Implemented |

### FR-AUTH — Authentication & Security

| ID | Original REQ-N | Description | Status |
|----|---------------|-------------|--------|
| FR-AUTH-001 | REQ-2 | User registration with email and username | Implemented |
| FR-AUTH-002 | REQ-2 | User login with email and password | Implemented |
| FR-AUTH-003 | — | TOTP two-factor authentication enrollment (QR code + manual secret) | Implemented |
| FR-AUTH-004 | — | TOTP two-factor authentication step-up verification at login | Implemented |
| FR-AUTH-005 | — | TOTP two-factor authentication unenrollment | Implemented |
| FR-AUTH-006 | — | Forgot-password / reset via email link (`PASSWORD_RECOVERY` flow) | Implemented |
| FR-AUTH-007 | — | JWT authentication guard on every protected API route and frontend route | Implemented |
| FR-AUTH-008 | REQ-3 | Encrypt user-submitted code before storage in the database | Not Implemented |

> **FR-AUTH-008 note:** Code is stored as plaintext; confidentiality is enforced instead by
> Row Level Security (NFR-SEC-001) and JWT authentication (FR-AUTH-007). See
> [Requirement Deviations](#requirement-deviations).

### FR-ANALYSIS — Code Analysis

| ID | Original REQ-N | Description | Status |
|----|---------------|-------------|--------|
| FR-ANALYSIS-001 | REQ-4, REQ-5 | Python AST parsing using the built-in `ast` module | Changed |
| FR-ANALYSIS-002 | REQ-5, REQ-6 | 48 PEP 8 / AST-based static checks (naming, style, imports, best practices, docs) | Changed |
| FR-ANALYSIS-003 | REQ-7 | AI-assisted bug prediction using OpenAI GPT-4o-mini | Changed |
| FR-ANALYSIS-004 | — | GPT-generated descriptive submission names for new submissions | Implemented |
| FR-ANALYSIS-005 | — | Reanalysis of an existing submission (updates code and results in place) | Implemented |
| FR-ANALYSIS-006 | — | CodeBERT confidence validation: fine-tuned binary classifier scores GPT predictions with P(buggy); low-confidence bugs flagged and skipped in score computation | Implemented |

### FR-REPORT — Results Reporting & Display

| ID | Original REQ-N | Description | Status |
|----|---------------|-------------|--------|
| FR-REPORT-001 | REQ-8 | Quality score (0–100) plus static findings with line number, severity, message, and suggested fix | Implemented |
| FR-REPORT-002 | REQ-8 | GPT-predicted bugs with description, severity, line number, and suggested fix | Implemented |
| FR-REPORT-003 | — | Sort findings and bugs by severity or line number, with ascending / descending direction toggle | Implemented |
| FR-REPORT-004 | — | Ignore / dismiss individual findings and predicted bugs | Implemented |
| FR-REPORT-005 | — | Hover a finding or bug to highlight the corresponding line in the editor | Implemented |
| FR-REPORT-006 | — | Export analysis results as self-contained HTML report with inline CSS, score card, findings table, AI bug cards, XSS-safe escaping, and print-ready styling | Implemented |
| FR-REPORT-007 | — | CodeBERT confidence badge on bug cards; min-confidence filter slider in results panel; flagged bugs dimmed and excluded from score | Implemented |
| FR-REPORT-008 | — | Resizable results panel with drag handle (220–600 px range); results panel header with icon and dynamic issue count | Implemented |
| FR-REPORT-009 | — | Severity left-border accents on findings and bug cards; hover feedback; staggered entrance animations on results load | Implemented |
| FR-REPORT-010 | — | Live-tracked line numbers on finding and bug cards via Monaco tracked decorations; stale state (dimmed, "line deleted" badge, jump/hover disabled) when a flagged line is deleted | Implemented |
| FR-REPORT-011 | — | "Show code" toggle on finding and bug cards reveals the original source line from the analyzed code snapshot | Implemented |

### FR-ACCT — Account Management

| ID | Original REQ-N | Description | Status |
|----|---------------|-------------|--------|
| FR-ACCT-001 | REQ-2 | View and update profile (username, avatar URL) | Implemented |
| FR-ACCT-002 | — | Upload profile avatar image to Supabase Storage (PNG / JPEG / WebP, ≤ 2 MB) | Implemented |
| FR-ACCT-003 | — | Change password (requires current password verification) | Implemented |
| FR-ACCT-004 | — | Delete account with full cascade cleanup of all submissions and reports | Implemented |
| FR-ACCT-005 | — | Invite a new user by email (sends Supabase invite email) | Implemented |
| FR-ACCT-006 | — | Export all user data (GDPR/CCPA JSON: profile + submissions + reports) | Implemented |
| FR-ACCT-007 | — | Sign out all devices via Supabase Auth | Implemented |
| FR-ACCT-008 | — | Report bug mailto link in account settings | Implemented |
| FR-ACCT-009 | — | Display "Member Since" date from profile | Implemented |
| FR-ACCT-010 | — | Two-factor authentication management section in account settings | Implemented |
| FR-ACCT-011 | — | Session refresh after profile updates to sync auth metadata | Implemented |

### FR-HIST — Submission History

| ID | Original REQ-N | Description | Status |
|----|---------------|-------------|--------|
| FR-HIST-001 | REQ-9 | Retrieve and display the authenticated user's past submissions with scores | Implemented |
| FR-HIST-002 | REQ-9 | Load a past submission's code and results into the editor and results panel | Implemented |
| FR-HIST-003 | — | Rename a submission | Implemented |
| FR-HIST-004 | — | Delete a submission | Implemented |
| FR-HIST-005 | — | Pin / star a submission so it sorts to the top of the sidebar | Implemented |
| FR-HIST-006 | — | Search and filter submissions by name in the sidebar | Implemented |
| FR-HIST-007 | — | Unsaved-edits confirmation: warns user when switching submissions after editing without re-analyzing | Implemented |

### FR-LOGIN — Login Page UI

| ID | Original REQ-N | Description | Status |
|----|---------------|-------------|--------|
| FR-LOGIN-001 | — | Hero landing page with animated GIF logo, wordmark, subtitle, and purple gradient background | Implemented |
| FR-LOGIN-002 | — | Glassmorphism auth card with sliding Log In / Sign Up toggle | Implemented |
| FR-LOGIN-003 | — | Show/hide password toggle (eye icon) with type attribute and ARIA label cycling | Implemented |
| FR-LOGIN-004 | — | Purple focus glow on form inputs | Implemented |
| FR-LOGIN-005 | — | "Learn More" scroll section with info cards, hover lift effect, scroll-triggered entrance animations, light mode support, and chevron scroll cue | Implemented |
| FR-LOGIN-006 | — | Auto-focus on email input on page load | Implemented |
| FR-LOGIN-007 | — | Terms of Service and Privacy Policy page links in login form footer | Implemented |

---

## Non-Functional Requirements

| ID | Original REQ-N | Category | Description | Status |
|----|---------------|----------|-------------|--------|
| NFR-PERF-001 | REQ-10 | Efficiency | Analysis results must be delivered within 5 seconds of submission | Implemented |
| NFR-USAB-001 | REQ-11 | Learnability | A new user must be able to complete their first full code analysis within 2 minutes of login | Implemented |
| NFR-USAB-002 | REQ-14 | Usability | Dashboard must display a visible loading state while backend analysis is in progress | Implemented |
| NFR-SEC-001 | REQ-12 | Confidentiality | Supabase Row Level Security ensures users can only access their own data | Implemented |
| NFR-SEC-002 | REQ-2 | Confidentiality | Passwords are stored as bcrypt hashes managed by Supabase Auth | Implemented |
| NFR-RELI-001 | REQ-13 | Reliability | System handles submissions up to 5,000 lines (100,000 characters) without degradation; GPT failures return static results rather than an error | Implemented |

---

## Requirement Deviations

The following requirements were delivered with implementations that differ from the original
specification.

### FR-AUTH-008 — Code Encryption (Not Implemented)

**Original (REQ-3):** The system shall encrypt all user-submitted source code before storage
in the PostgreSQL database.

**Actual:** Code is stored as plaintext. Data confidentiality is enforced through:
- Supabase Row Level Security (`NFR-SEC-001`) — database policies prevent cross-user access
- JWT authentication on every endpoint (`FR-AUTH-007`) — unauthenticated requests are rejected at the API layer

**Reason:** At-rest encryption was descoped in favour of Supabase's built-in RLS, which
satisfies the confidentiality requirement (REQ-12) without the performance and key-management
overhead of application-layer encryption.

### FR-ANALYSIS-001 — AST Parsing (Changed)

**Original (REQ-4):** The system shall use a `CodeParser` class to generate an `ASTObject`
representing the code's hierarchy and symbol table.

**Actual:** Python's built-in `ast` module is used directly inside `analysis_engine.py`.
There is no separate `CodeParser` class or `ASTObject` wrapper; the AST is an intermediate
artefact consumed immediately by the 24 static-check functions.

### FR-ANALYSIS-002 — Static Analysis Checks (Changed)

**Original (REQ-5):** The `StaticEngine` shall calculate cyclomatic complexity and identify
dead code or bloated classes.

**Actual:** The analysis engine (`analysis_engine.py`) implements 48 PEP 8 / AST-based
checks covering naming conventions, code style, import organisation, documentation, and
best practices. Cyclomatic complexity and dead-code detection are not included.

### FR-ANALYSIS-003 — AI Bug Prediction (Changed)

**Original (REQ-7):** The system shall utilise an AI model (e.g., CodeBERT) to identify
risky patterns and predict potential bugs based on historical data.

**Actual:** Bug prediction is performed by OpenAI GPT-4o-mini via the Chat Completions API
(`gpt_predictor.py`). The model is not fine-tuned on historical data; it uses a structured
prompt that includes the static-analysis findings as context to avoid duplication.
