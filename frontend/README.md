# CodePulse Frontend

React frontend for the CodePulse code quality and bug prediction dashboard.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 18 (functional components / Hooks) |
| Routing | React Router v6 |
| Auth | Supabase Auth (`@supabase/supabase-js`) |
| Code Editor | Monaco Editor (`@monaco-editor/react`) |
| Styling | Plain CSS (CSS files per feature area) |
| Build | Create React App (`react-scripts`) |

---

## Project Structure

```
frontend/
├── public/
│   └── index.html              # HTML shell
└── src/
    ├── index.js                # React entry point
    ├── App.js                  # Router and AuthProvider setup
    ├── setupTests.js           # Jest / Testing Library global setup
    ├── services/
    │   ├── supabaseClient.js   # Supabase client singleton
    │   ├── analysisService.js  # analyzeCode() — POST /api/v1/analyze (with name + reanalyze)
    │   ├── submissionService.js # Submission CRUD (list, save, rename, delete, pin)
    │   └── accountService.js   # Account CRUD (profile, avatar, password, delete)
    ├── context/
    │   └── AuthContext.js      # Auth state, useAuth hook, signIn/signUp/signOut, refreshSession
    ├── components/
    │   ├── ProtectedRoute.js   # Redirects unauthenticated users to /login
    │   ├── CodeEditor.js       # Monaco editor + Copy button + Run Analysis button; severity-colored line highlights (togglable); gear icon settings panel (font size, tab size, word wrap, ligatures, whitespace, bracket colors, smooth scroll, folding, line highlight, Ctrl+scroll zoom, severity highlights) persisted to localStorage
    │   ├── ResultsPanel.js     # SVG score ring, resizable panel (220–600px), static findings and AI bug cards with severity borders + hover effects + entrance animations; SortControls; per-item ignore/dismiss; header icon + dynamic issue count
    │   ├── BugCard.js          # Collapsible AI bug prediction card with severity border accent, ignore and hover-highlight support, CodeBERT confidence badge
    │   ├── HelpModal.js        # "How CodePulse Works" modal — getting started, score, static analysis, AI predictions, CodeBERT confidence tiers, tips
    │   ├── ProfileDropdown.js  # User avatar and dropdown menu (links to /account)
    │   ├── SubmissionSidebar.js # Collapsible sidebar with rename/delete/pin via kebab menu; skips API call if name unchanged
    │   ├── TwoFactorSection.js # TOTP 2FA enrollment/unenrollment — QR code display, verify, disable
    │   └── Toast.js            # Toast notification system (ToastProvider + useToast)
    ├── pages/
    │   ├── LoginPage.js        # Log In / Sign Up sliding toggle / Forgot Password; MFA step-up (TOTP); purple focus glow; learn-more cards with hover lift + scroll-triggered entrance + light mode support; chevron scroll cue
    │   ├── DashboardPage.js    # Dashboard shell — editor + results + submission naming
    │   ├── AccountPage.js      # Account settings — profile, avatar (96px), password, delete; section title icons, lock icons on read-only fields, save confirmation flash
    │   └── ResetPasswordPage.js # Password reset form — validates token, updates password
    └── styles/
        ├── auth.css            # Login/sign-up form styles — sliding toggle, focus glow, learn-more hover/entrance/light-mode, chevron scroll cue
        ├── dashboard.css       # Dashboard + toast + submission naming + resizable results panel + SVG score ring + severity borders/highlights + entrance animations
        └── account.css         # Account settings page — section icons, lock icon, larger avatar, save confirmation flash
```

---

## Routes

| Path | Access | Description |
|------|--------|-------------|
| `/` | Public | Redirects to `/dashboard` |
| `/login` | Public | Log In and Sign Up forms |
| `/reset-password` | Public | Set a new password after clicking a reset email link |
| `/dashboard` | Protected | Main dashboard — requires authentication |
| `/account` | Protected | Account settings — profile, avatar, password, delete |

---

## Authentication

Authentication is handled entirely by Supabase Auth. Passwords are never stored in the application database.

- **Sign Up** — creates a Supabase Auth user and automatically creates a matching row in the `profiles` table via a database trigger
- **Log In** — establishes a session; the JWT (`session.access_token`) is available via `useAuth()` for passing to backend API calls
- **Session persistence** — Supabase persists the session to `localStorage`; users remain logged in across page refreshes

```js
// Access auth state from any component
const { user, session, signOut } = useAuth()

// JWT for backend API calls
const token = session.access_token
```

---

## Local Setup

### Prerequisites

- Node.js 24+
- A configured Supabase project (see `backend/database/schema.sql`)

### Installation

```bash
cd frontend
npm install
cp .env.example .env   # Fill in your Supabase URL and anon key
npm start              # Runs at http://localhost:3000
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `REACT_APP_SUPABASE_URL` | Your Supabase project URL |
| `REACT_APP_SUPABASE_ANON_KEY` | Your Supabase publishable (anon) key |
| `REACT_APP_API_URL` | Backend API base URL (default: `http://localhost:8000`) |

Copy `.env.example` to `.env` and fill in the values. Never commit `.env`.

---

## Testing

Tests use [React Testing Library](https://testing-library.com/react) and Jest (bundled with CRA). Supabase is mocked in all tests — no real network calls are made.

```bash
npm test                  # Run in watch mode
npm test -- --watchAll=false   # Run once and exit (used in CI)
```

| Test File | Coverage |
|-----------|----------|
| `components/__tests__/ProtectedRoute.test.js` | Loading state, unauthenticated redirect, authenticated render (3 tests) |
| `context/__tests__/AuthContext.test.js` | Auth lifecycle, signIn / signUp / signOut calls (4 tests) |
| `pages/__tests__/LoginPage.test.js` | Form toggle, submission handlers, error display, show/hide password, learn-more section, remember me, confirm password, password strength, ToS links, OAuth; forgot password flow; MFA step-up (45 tests) |
| `components/__tests__/TwoFactorSection.test.js` | No-factor state, enrolled state, enroll + QR display, secret display, verify, verify error, success state, disable, re-enable, disable error (11 tests) |
| `pages/__tests__/ResetPasswordPage.test.js` | Loading state, PASSWORD_RECOVERY trigger, validation, updateUser call, toast + navigation, error on expired link, submit disabled while pending (8 tests) |
| `components/__tests__/CodeEditor.test.js` | Renders editor, button click fires onRun, disabled during loading, copy button disabled when empty; gear button ARIA, panel open/close, outside-click dismiss, setting change, toggle flip, localStorage persist, localStorage init (11 tests) |
| `components/__tests__/ResultsPanel.test.js` | Idle, loading, error, score, findings, bugs (expand/collapse), empty states, ignore/dismiss, severity hover line highlight, severity sort, line sort, tiebreaker, null-line sort, confidence filter, flagged bugs, export button, resizable panel (43 tests) |
| `components/__tests__/SubmissionSidebar.test.js` | Render names, fallback, search, rename no-op, rename, delete, pin/star, collapse (12 tests) |
| `components/__tests__/InviteModal.test.js` | Render, empty-email disable, submit handler, success toast, error display, cancel, backdrop click, loading state (9 tests) |
| `utils/__tests__/generateReport.test.js` | Content inclusion, score colors, XSS escaping, empty arrays, naming, complete HTML structure (10 tests) |
| `pages/__tests__/AccountPage.test.js` | Profile load/display, username validation, password change, avatar, delete modal, report bug, member since, data export, sign out all (16 tests) |

172 tests, all passing.

---

## CI/CD

The frontend CI workflow runs automatically on every push and pull request to `main` that touches `frontend/**`.

**Workflow:** `.github/workflows/frontend-ci.yml`

| Step | Command |
|------|---------|
| Install | `npm ci` |
| Audit | `npm audit --audit-level=critical` |
| Test | `npm test -- --watchAll=false --ci` |
| Build | `npm run build` |

A pull request cannot be merged if any step fails.

**Required GitHub Secrets** (Settings → Secrets → Actions):

| Secret | Description |
|--------|-------------|
| `REACT_APP_SUPABASE_URL` | Supabase project URL (used in the build step) |
| `REACT_APP_SUPABASE_ANON_KEY` | Supabase publishable key (used in the build step) |

---

## Requirements

See [REQUIREMENTS.md](REQUIREMENTS.md) for the full list of functional and non-functional
requirements with unique IDs, descriptions, and implementation file locations.

---

## Implementation Status

| Feature | Status |
|---------|--------|
| React app bootstrap | Done |
| Supabase client setup | Done |
| Auth context + session observer | Done |
| Login / Sign Up UI (green success banner on account creation) | Done |
| Protected routes | Done |
| JWT token hand-off pattern | Done |
| Dashboard UI | Done |
| Code editor / submission flow | Done |
| Results display (Severity/Line field selector pills + ↑/↓ direction toggle; two-key combined sort; resets on submission change) | Done |
| Copy-to-clipboard button in editor toolbar | Done |
| Hover finding/bug to highlight corresponding editor line (severity-colored, togglable) | Done |
| Click-to-jump from finding/bug card to editor line | Done |
| Ignore/dismiss individual findings and bugs | Done |
| Account settings page (profile, avatar, password, 2FA, report bug, data export, sign out all, delete) | Done |
| Submission sidebar (rename, delete, pin/star via kebab menu) | Done |
| Submission naming (name input, GPT auto-generation) | Done |
| Toast notification system | Done |
| Session refresh after profile updates | Done |
| Dark/light theme toggle (including login learn-more section) | Done |
| Resizable results panel (drag handle, 220–600px) | Done |
| SVG score ring (arc fills proportionally, severity-colored text) | Done |
| Severity left-border accents on findings and bug cards | Done |
| Hover feedback on findings and bug cards | Done |
| Staggered entrance animations on results | Done |
| Results panel header icon + dynamic issue count | Done |
| HTML report export (self-contained, printable, XSS-safe, purple branding) | Done |
| Login page — sliding toggle, focus glow, card hover lift, scroll entrance animations, chevron scroll cue, remember me, confirm password, password strength, Google/GitHub OAuth, ToS/Privacy links | Done |
| Account page — section title icons, lock icons on read-only fields, larger avatar, save confirmation flash | Done |
| CodeBERT confidence badge on bug cards + min-confidence filter slider in results panel (flagged bugs dimmed, excluded from score) | Done |
| HelpModal — in-dashboard "?" button explaining pipeline, scoring, and CodeBERT tiers | Done |
| Invite user modal | Done |
| Terms of Service and Privacy Policy pages | Done |
| Password reset page | Done |
