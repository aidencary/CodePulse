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
    │   ├── CodeEditor.js       # Monaco editor + submission name input + Run Analysis button
    │   ├── ResultsPanel.js     # Score circle, static findings, AI bug prediction cards
    │   ├── ProfileDropdown.js  # User avatar and dropdown menu (links to /account)
    │   ├── SubmissionSidebar.js # Collapsible sidebar with rename/delete/pin via kebab menu
    │   └── Toast.js            # Toast notification system (ToastProvider + useToast)
    ├── pages/
    │   ├── LoginPage.js        # Log In / Sign Up form (toggled)
    │   ├── DashboardPage.js    # Dashboard shell — editor + results + submission naming
    │   └── AccountPage.js      # Account settings — profile, avatar, password, delete
    └── styles/
        ├── auth.css            # Login/sign-up form styles
        ├── dashboard.css       # Dashboard + toast + submission naming styles
        └── account.css         # Account settings page styles
```

---

## Routes

| Path | Access | Description |
|------|--------|-------------|
| `/` | Public | Redirects to `/dashboard` |
| `/login` | Public | Log In and Sign Up forms |
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

- Node.js 20+
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
| `components/__tests__/ProtectedRoute.test.js` | Loading state, unauthenticated redirect, authenticated render |
| `context/__tests__/AuthContext.test.js` | Auth lifecycle, signIn / signUp / signOut calls |
| `pages/__tests__/LoginPage.test.js` | Form toggle, submission handlers, error display |
| `components/__tests__/CodeEditor.test.js` | Renders editor, button click fires onRun, disabled during loading |
| `components/__tests__/ResultsPanel.test.js` | Idle, loading, error, score, findings, predicted bugs (expand/collapse), empty states (17 tests) |
| `components/__tests__/SubmissionSidebar.test.js` | Render names, fallback, search, rename, delete, pin/star, collapse (11 tests) |
| `pages/__tests__/AccountPage.test.js` | Profile load/display, username validation, password change, delete modal (10 tests) |

53 tests, all passing.

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

## Implementation Status

| Feature | Status |
|---------|--------|
| React app bootstrap | Done |
| Supabase client setup | Done |
| Auth context + session observer | Done |
| Login / Sign Up UI | Done |
| Protected routes | Done |
| JWT token hand-off pattern | Done |
| Dashboard UI | Done |
| Code editor / submission flow | Done |
| Results display | Done |
| Account settings page (profile, avatar, password, delete) | Done |
| Submission sidebar (rename, delete, pin/star via kebab menu) | Done |
| Submission naming (name input, GPT auto-generation) | Done |
| Toast notification system | Done |
| Session refresh after profile updates | Done |
| Dark/light theme toggle | Done |
