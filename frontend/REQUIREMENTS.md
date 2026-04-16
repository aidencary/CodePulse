# CodePulse Frontend — Requirements

This document defines every functional and non-functional requirement implemented in the
CodePulse React frontend. Each requirement has a unique ID, description, and the source
file(s) where it is implemented. Requirement IDs are referenced by test cases in
[TESTING.md](../TESTING.md) (pattern `TC-{MODULE}-{NNN}`).

---

## ID Scheme

| Prefix | Module |
|--------|--------|
| `FR-DASH-NNN` | Dashboard / UI shell |
| `FR-AUTH-NNN` | Authentication & security |
| `FR-ANALYSIS-NNN` | Code analysis (submission flow) |
| `FR-REPORT-NNN` | Results reporting & display |
| `FR-ACCT-NNN` | Account management |
| `FR-HIST-NNN` | Submission history |
| `NFR-PERF-NNN` | Performance |
| `NFR-USAB-NNN` | Usability |
| `NFR-SEC-NNN` | Security / confidentiality |
| `NFR-RELI-NNN` | Reliability |

---

## Functional Requirements

### FR-DASH — Dashboard / UI Shell

| ID | Description | File(s) |
|----|-------------|---------|
| FR-DASH-001 | Web dashboard with Monaco code editor for pasting and submitting Python source code, including copy-to-clipboard button, settings gear panel (font size, tab size, word wrap, ligatures, whitespace, bracket colors, smooth scroll, folding, line highlight, zoom, severity highlights), and Run Analysis button with sparkle animation | `src/components/CodeEditor.js` |
| FR-DASH-002 | Dashboard remains interactive and displays skeleton loading state while backend analysis is in progress; Run Analysis button is disabled during loading | `src/components/CodeEditor.js`, `src/components/ResultsPanel.js` |
| FR-DASH-003 | Dark / light theme toggle with `localStorage` persistence (`cp-theme` key); moon icon in dark mode, sun icon in light mode | `src/pages/DashboardPage.js`, `src/styles/dashboard.css` |
| FR-DASH-004 | Three-column layout: collapsible submissions sidebar (240 px open / 52 px mini-bar), Monaco editor, and resizable results panel | `src/pages/DashboardPage.js`, `src/components/SubmissionSidebar.js`, `src/components/ResultsPanel.js` |
| FR-DASH-005 | Invite new users by email via in-dashboard modal | `src/components/InviteModal.js`, `src/pages/DashboardPage.js` |
| FR-DASH-006 | Line-highlight orchestration: hovering a finding or bug in the results panel highlights the corresponding line in the editor with severity-appropriate color | `src/pages/DashboardPage.js`, `src/components/ResultsPanel.js`, `src/components/BugCard.js`, `src/components/CodeEditor.js` |
| FR-DASH-007 | Click-to-jump: clicking a finding or bug card scrolls the editor to the corresponding line number | `src/pages/DashboardPage.js`, `src/components/ResultsPanel.js`, `src/components/BugCard.js`, `src/components/CodeEditor.js` |
| FR-DASH-008 | Help modal ("?") button in dashboard nav explaining pipeline, scoring, static analysis, AI predictions, CodeBERT confidence tiers, and tips | `src/components/HelpModal.js`, `src/pages/DashboardPage.js` |
| FR-DASH-009 | Profile dropdown in navbar with hash-based avatar color, links to Account page and Sign Out | `src/components/ProfileDropdown.js` |

### FR-AUTH — Authentication & Security

| ID | Description | File(s) |
|----|-------------|---------|
| FR-AUTH-001 | User registration with email, password, and username via Supabase Auth; confirm password field with match validation; password strength indicator (Weak / Fair / Strong) | `src/pages/LoginPage.js`, `src/context/AuthContext.js` |
| FR-AUTH-002 | User login with email and password; session persistence via Supabase `localStorage`; "Remember Me" checkbox controls session-only vs persistent mode; auth state observer with cleanup on unmount | `src/pages/LoginPage.js`, `src/context/AuthContext.js` |
| FR-AUTH-003 | TOTP two-factor authentication enrollment: generates QR code and manual secret for authenticator app setup | `src/components/TwoFactorSection.js` |
| FR-AUTH-004 | TOTP two-factor authentication step-up verification at login: 6-digit code input after successful credential check when AAL2 is required | `src/pages/LoginPage.js`, `src/components/TwoFactorSection.js` |
| FR-AUTH-005 | TOTP two-factor authentication unenrollment with status display | `src/components/TwoFactorSection.js` |
| FR-AUTH-006 | Forgot-password flow: email input form, `resetPasswordForEmail` call, success/error feedback, back-to-login navigation; dedicated reset-password page that listens for `PASSWORD_RECOVERY` auth event and calls `updateUser` | `src/pages/LoginPage.js`, `src/pages/ResetPasswordPage.js` |
| FR-AUTH-007 | Protected route guard: redirects unauthenticated users to `/login`; shows loading indicator while auth state initializes; JWT token passed as Bearer header on all API calls | `src/components/ProtectedRoute.js`, `src/services/analysisService.js`, `src/services/accountService.js`, `src/services/submissionService.js` |
| FR-AUTH-008 | Google and GitHub OAuth login buttons on the login page | `src/pages/LoginPage.js` |

### FR-ANALYSIS — Code Analysis (Submission Flow)

| ID | Description | File(s) |
|----|-------------|---------|
| FR-ANALYSIS-001 | Submit code to `POST /api/v1/analyze` with Bearer JWT; receive static findings, GPT-predicted bugs, quality score, and submission name | `src/services/analysisService.js`, `src/pages/DashboardPage.js` |
| FR-ANALYSIS-004 | Submission naming: user-provided name input in editor toolbar, or GPT-generated name if left blank | `src/components/CodeEditor.js`, `src/pages/DashboardPage.js` |
| FR-ANALYSIS-005 | Reanalysis of an existing submission by passing `submission_id` to the analyze endpoint; updates code and results in place | `src/services/analysisService.js`, `src/pages/DashboardPage.js` |

### FR-REPORT — Results Reporting & Display

| ID | Description | File(s) |
|----|-------------|---------|
| FR-REPORT-001 | Display quality score (0-100) via SVG score ring with severity-colored arc and text; show static findings with issue type, line number, severity badge, and message; show summary text; show idle/empty/error states | `src/components/ResultsPanel.js` |
| FR-REPORT-002 | Display GPT-predicted bugs in expandable cards with bug type, severity badge, description, line number, suggested fix, CodeBERT confidence pill, and flagged-bug dimming | `src/components/ResultsPanel.js`, `src/components/BugCard.js` |
| FR-REPORT-003 | Sort findings and bugs by Severity or Line Number with ascending/descending direction toggle; two-key combined sort with tiebreaker; null line numbers sort last; sort resets on submission change | `src/components/ResultsPanel.js` |
| FR-REPORT-004 | Ignore / dismiss individual findings and predicted bugs; ignored items reappear when results are reset (new submission loaded) | `src/components/ResultsPanel.js`, `src/components/BugCard.js` |
| FR-REPORT-005 | Hover a finding or bug to highlight the corresponding editor line via `onHoverLine` callback; no highlight when bug has no line number | `src/components/ResultsPanel.js`, `src/components/BugCard.js` |
| FR-REPORT-006 | Export analysis results as self-contained HTML report with inline CSS, score card, findings table, AI bug cards, XSS-safe escaping, and print-ready styling | `src/utils/generateReport.js`, `src/components/ResultsPanel.js` |
| FR-REPORT-007 | CodeBERT confidence badge on bug cards; min-confidence filter slider in results panel; flagged bugs dimmed and excluded from score | `src/components/ResultsPanel.js`, `src/components/BugCard.js` |
| FR-REPORT-008 | Resizable results panel with drag handle (220-600 px range); results panel header with icon and dynamic issue count | `src/components/ResultsPanel.js` |
| FR-REPORT-009 | Severity left-border accents on findings and bug cards; hover feedback with subtle lift/glow; staggered entrance animations on results load | `src/components/ResultsPanel.js`, `src/components/BugCard.js`, `src/styles/dashboard.css` |

### FR-ACCT — Account Management

| ID | Description | File(s) |
|----|-------------|---------|
| FR-ACCT-001 | View and update profile: read-only email and role fields (lock icons), editable username (3-20 chars, alphanumeric + underscore/hyphen); save confirmation flash | `src/pages/AccountPage.js`, `src/services/accountService.js` |
| FR-ACCT-002 | Upload profile avatar image (PNG / JPEG / WebP, max 2 MB) with 96 px preview | `src/pages/AccountPage.js`, `src/services/accountService.js` |
| FR-ACCT-003 | Change password with current password verification, new password (8-128 chars), and confirm password match validation | `src/pages/AccountPage.js`, `src/services/accountService.js` |
| FR-ACCT-004 | Delete account with confirmation modal requiring username match before enabling the delete button; cascades all user data | `src/pages/AccountPage.js`, `src/services/accountService.js` |
| FR-ACCT-005 | Invite a new user by email via modal: email input, loading state, success toast, error display | `src/components/InviteModal.js`, `src/services/accountService.js` |
| FR-ACCT-006 | Download data export (GDPR/CCPA JSON) of all user data (profile + submissions + reports) | `src/pages/AccountPage.js`, `src/services/accountService.js` |
| FR-ACCT-007 | Sign out all devices via Supabase Auth | `src/pages/AccountPage.js` |
| FR-ACCT-008 | Report bug mailto link in account settings | `src/pages/AccountPage.js` |
| FR-ACCT-009 | Display "Member Since" date from profile | `src/pages/AccountPage.js` |
| FR-ACCT-010 | Two-factor authentication management section (delegates to TwoFactorSection) | `src/pages/AccountPage.js`, `src/components/TwoFactorSection.js` |
| FR-ACCT-011 | Session refresh after profile updates to sync auth metadata | `src/context/AuthContext.js`, `src/pages/AccountPage.js` |

### FR-HIST — Submission History

| ID | Description | File(s) |
|----|-------------|---------|
| FR-HIST-001 | Retrieve and display authenticated user's past submissions with names and scores in sidebar; falls back to first code line when name is null | `src/components/SubmissionSidebar.js`, `src/services/submissionService.js` |
| FR-HIST-002 | Load a past submission's code and results into the editor and results panel on click | `src/pages/DashboardPage.js`, `src/services/submissionService.js` |
| FR-HIST-003 | Rename a submission via inline editing (double-click or kebab menu); Enter to save, Escape to cancel; skips API call if name unchanged | `src/components/SubmissionSidebar.js`, `src/services/submissionService.js` |
| FR-HIST-004 | Delete a submission with centered confirmation modal via kebab menu | `src/components/SubmissionSidebar.js`, `src/services/submissionService.js` |
| FR-HIST-005 | Pin / star a submission via kebab menu; pinned submissions sort to top with star icon; toggle pin/unpin | `src/components/SubmissionSidebar.js`, `src/services/submissionService.js` |
| FR-HIST-006 | Search and filter submissions by name in the sidebar search input | `src/components/SubmissionSidebar.js` |

### FR-LOGIN — Login Page UI

| ID | Description | File(s) |
|----|-------------|---------|
| FR-LOGIN-001 | Hero landing page with animated GIF logo, wordmark, subtitle, and purple gradient background | `src/pages/LoginPage.js`, `src/styles/auth.css` |
| FR-LOGIN-002 | Glassmorphism auth card with sliding Log In / Sign Up toggle | `src/pages/LoginPage.js`, `src/styles/auth.css` |
| FR-LOGIN-003 | Show/hide password toggle (eye icon) with type attribute and ARIA label cycling | `src/pages/LoginPage.js` |
| FR-LOGIN-004 | Purple focus glow on form inputs | `src/styles/auth.css` |
| FR-LOGIN-005 | "Learn More" scroll section with 6 info cards, hover lift effect, scroll-triggered entrance animations, light mode support, and chevron scroll cue | `src/pages/LoginPage.js`, `src/styles/auth.css` |
| FR-LOGIN-006 | Auto-focus on email input on page load | `src/pages/LoginPage.js` |
| FR-LOGIN-007 | Terms of Service and Privacy Policy page links in login form footer | `src/pages/LoginPage.js`, `src/pages/TermsPage.js`, `src/pages/PrivacyPage.js` |

---

## Non-Functional Requirements

| ID | Category | Description | File(s) |
|----|----------|-------------|---------|
| NFR-USAB-001 | Learnability | A new user can complete their first full code analysis within 2 minutes of login; clear button labels, loading indicators, and placeholder states guide the user | `src/components/CodeEditor.js`, `src/components/ResultsPanel.js`, `src/components/HelpModal.js` |
| NFR-USAB-002 | Usability | Dashboard displays visible skeleton loading state with `aria-label` while backend analysis is in progress | `src/components/ResultsPanel.js` |
| NFR-USAB-003 | Accessibility | Toast notifications use `aria-live="polite"` for screen reader support; buttons have appropriate ARIA attributes | `src/components/Toast.js`, `src/components/CodeEditor.js` |
| NFR-USAB-004 | Responsiveness | Results panel is resizable (220-600 px) via drag handle; sidebar collapses to 52 px mini-bar; editor fills remaining space | `src/components/ResultsPanel.js`, `src/components/SubmissionSidebar.js` |
| NFR-SEC-001 | Confidentiality | All API calls include Bearer JWT in Authorization header; protected routes redirect unauthenticated users; OAuth redirects use hardcoded `window.location.origin` paths | `src/components/ProtectedRoute.js`, `src/services/analysisService.js`, `src/services/accountService.js` |
| NFR-SEC-002 | XSS Prevention | HTML report export escapes all user-provided strings (including `line_number`) via `escapeHTML()` to prevent XSS in generated files | `src/utils/generateReport.js` |
| NFR-RELI-001 | Reliability | Error states display user-friendly messages in results panel; toast notifications for success/failure feedback; graceful handling of API errors | `src/components/ResultsPanel.js`, `src/components/Toast.js` |
| NFR-PERF-001 | Performance | Editor settings persisted to `localStorage` to avoid re-configuration; submission sidebar exposes `refresh()` via `useImperativeHandle` to avoid full re-mount; `useMemo` for expensive computations | `src/components/CodeEditor.js`, `src/components/SubmissionSidebar.js` |
| NFR-PERF-002 | Performance | Staggered entrance animations on results load prevent layout thrashing; severity highlights togglable in settings to reduce editor repaints | `src/components/ResultsPanel.js`, `src/components/CodeEditor.js`, `src/styles/dashboard.css` |

---

## Test Coverage

172 frontend tests across 11 test suites. See [TESTING.md](../TESTING.md) for the full
test matrix mapping `TC-{MODULE}-{NNN}` IDs to requirements.

| Test Suite | Tests | Requirements Covered |
|-----------|-------|---------------------|
| `ProtectedRoute.test.js` | 3 | FR-AUTH-007, NFR-USAB-001 |
| `CodeEditor.test.js` | 11 | FR-DASH-001, FR-DASH-002, NFR-USAB-001 |
| `ResultsPanel.test.js` | 28 | FR-REPORT-001 through FR-REPORT-005, FR-DASH-002, FR-DASH-006, NFR-USAB-001, NFR-RELI-001 |
| `SubmissionSidebar.test.js` | 12 | FR-HIST-001, FR-HIST-003 through FR-HIST-006, FR-DASH-004 |
| `InviteModal.test.js` | 9 | FR-ACCT-005, FR-DASH-005 |
| `TwoFactorSection.test.js` | 11 | FR-AUTH-003, FR-AUTH-004, FR-AUTH-005 |
| `AuthContext.test.js` | 4 | FR-AUTH-001, FR-AUTH-002 |
| `LoginPage.test.js` | 17 | FR-AUTH-001, FR-AUTH-002, FR-AUTH-004, FR-AUTH-006 |
| `AccountPage.test.js` | 10 | FR-ACCT-001 through FR-ACCT-004 |
| `ResetPasswordPage.test.js` | 8 | FR-AUTH-006 |
| `generateReport.test.js` | 10 | FR-REPORT-006, NFR-SEC-002 |

> **Note:** Test counts above reflect the `LoginPage.test.js` split — 17 tests in the login
> page suite cover login, signup, forgot-password, and MFA flows. The remaining frontend
> tests (49 additional across `ProtectedRoute`, `CodeEditor`, `ResultsPanel`, `SubmissionSidebar`,
> `InviteModal`, `TwoFactorSection`, `AuthContext`, `AccountPage`, `ResetPasswordPage`,
> `generateReport`) bring the total to 172.
