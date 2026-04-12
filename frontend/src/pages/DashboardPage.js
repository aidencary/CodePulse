import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { analyzeCode } from '../services/analysisService'
import { getSubmissionDetail } from '../services/submissionService'
import CodeEditor from '../components/CodeEditor'
import ResultsPanel from '../components/ResultsPanel'
import SubmissionSidebar from '../components/SubmissionSidebar'
import ProfileDropdown from '../components/ProfileDropdown'
import InviteModal from '../components/InviteModal'
import HelpModal from '../components/HelpModal'
import '../styles/dashboard.css'

function SunIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="5" />
      <line x1="12" y1="1"  x2="12" y2="3" />
      <line x1="12" y1="21" x2="12" y2="23" />
      <line x1="4.22" y1="4.22"   x2="5.64"  y2="5.64" />
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      <line x1="1"  y1="12" x2="3"  y2="12" />
      <line x1="21" y1="12" x2="23" y2="12" />
      <line x1="4.22"  y1="19.78" x2="5.64"  y2="18.36" />
      <line x1="18.36" y1="5.64"  x2="19.78" y2="4.22" />
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  )
}

// FR-DASH-001
// FR-DASH-004
function DashboardPage() {
  const { user, session } = useAuth()
  const sidebarRef = useRef(null)

  const [code, setCode] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeId, setActiveId] = useState(null)
  const [hoveredLine, setHoveredLine] = useState(null) // null or { line, severity }
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [theme, setTheme] = useState(
    () => localStorage.getItem('cp-theme') || 'dark'
  )
  const [submissionName, setSubmissionName] = useState(null)
  const [inviteOpen, setInviteOpen] = useState(false)
  const [helpOpen, setHelpOpen] = useState(false)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('cp-theme', theme)
  }, [theme])

  // FR-DASH-003
  const toggleTheme = () => setTheme(t => (t === 'dark' ? 'light' : 'dark'))

  const username =
    user?.user_metadata?.username || user?.email?.split('@')[0] || 'user'

  // FR-DASH-001
  // FR-DASH-002
  const handleRun = async (currentCode) => {
    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const data = await analyzeCode(
        currentCode, session.access_token, undefined, activeId
      )
      setResults(data)
      setActiveId(data.submission_id)
      setSubmissionName(data.name || null)
      sidebarRef.current?.refresh()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectSubmission = async (submission) => {
    if (!submission) {
      setCode('')
      setResults(null)
      setError(null)
      setActiveId(null)
      setSubmissionName(null)
      return
    }

    setCode(submission.code)
    setError(null)
    setActiveId(submission.submission_id)
    setSubmissionName(submission.name || null)

    // Fetch full analysis (findings + predicted bugs) from the database.
    try {
      const detail = await getSubmissionDetail(submission.submission_id)
      const report = detail.analysis_reports
      if (report) {
        setResults({
          overall_score: report.overall_score,
          summary: report.summary,
          findings: (report.findings || []).map((f) => ({
            ...f,
            severity: f.line_severity ?? f.severity,
          })),
          predicted_bugs: report.predicted_bugs || [],
        })
      } else {
        setResults(null)
      }
    } catch {
      setResults(null)
    }
  }

  return (
    <div className="dashboard-page">
      <SubmissionSidebar
        ref={sidebarRef}
        onSelect={handleSelectSubmission}
        activeId={activeId}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onOpen={() => setSidebarOpen(true)}
      />

      {/* FR-DASH-005 */}
      {inviteOpen && <InviteModal onClose={() => setInviteOpen(false)} />}
      {helpOpen && <HelpModal onClose={() => setHelpOpen(false)} />}

      <div className="dashboard-right">
        <nav className="dashboard-nav">
          <span
            className="nav-brand"
            onClick={() => handleSelectSubmission(null)}
            role="button"
            tabIndex={0}
          >CodePulse</span>
          <div className="nav-user">
            <button
              className="nav-help-btn"
              onClick={() => setHelpOpen(true)}
              aria-label="How CodePulse works"
              title="How CodePulse works"
              type="button"
            >
              ?
            </button>
            <button
              className="nav-invite-btn"
              onClick={() => setInviteOpen(true)}
              type="button"
            >
              + Invite
            </button>
            <span className="nav-username">{username}</span>
            <ProfileDropdown user={user} />
            <button
              className="theme-toggle"
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? <MoonIcon /> : <SunIcon />}
            </button>
          </div>
        </nav>

        <main className="dashboard-main">
          <CodeEditor
            code={code}
            onCodeChange={setCode}
            onRun={handleRun}
            loading={loading}
            isDark={theme === 'dark'}
            highlightLine={hoveredLine}
          />
          {/* FR-DASH-006 FR-REPORT-005 */}
          <ResultsPanel results={results} loading={loading} error={error} onHoverLine={setHoveredLine} submissionName={submissionName} />
        </main>
      </div>
    </div>
  )
}

export default DashboardPage
