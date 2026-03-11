import { useRef, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { analyzeCode } from '../services/analysisService'
import { saveSubmission } from '../services/submissionService'
import CodeEditor from '../components/CodeEditor'
import ResultsPanel from '../components/ResultsPanel'
import SubmissionSidebar from '../components/SubmissionSidebar'
import ProfileDropdown from '../components/ProfileDropdown'
import '../styles/dashboard.css'

function DashboardPage() {
  const { user, session } = useAuth()
  const sidebarRef = useRef(null)

  const [code, setCode] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeId, setActiveId] = useState(null)

  const username =
    user?.user_metadata?.username || user?.email?.split('@')[0] || 'user'

  const handleRun = async (currentCode) => {
    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const data = await analyzeCode(currentCode, session.access_token)
      setResults(data)

      const saved = await saveSubmission(user.id, currentCode)
      setActiveId(saved.submission_id)
      sidebarRef.current?.refresh()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectSubmission = (submission) => {
    if (!submission) {
      setCode('')
      setResults(null)
      setError(null)
      setActiveId(null)
      return
    }
    setCode(submission.code)
    setResults(submission.analysis_reports ?? null)
    setError(null)
    setActiveId(submission.submission_id)
  }

  return (
    <div className="dashboard-page">
      {/* Pure-CSS dark toggle — must be first child, curtain must be last */}
      <input type="checkbox" id="dark-toggle" className="dark-toggle-input" />

      <nav className="dashboard-nav">
        <span className="nav-brand">CodePulse</span>
        <div className="nav-user">
          <span className="nav-username">{username}</span>
          <ProfileDropdown user={user} />
          <label htmlFor="dark-toggle" className="dark-toggle-label">
            <span className="sr">Toggle dark mode</span>
          </label>
        </div>
      </nav>

      <main className="dashboard-main">
        <SubmissionSidebar
          ref={sidebarRef}
          onSelect={handleSelectSubmission}
          activeId={activeId}
        />
        <CodeEditor
          code={code}
          onCodeChange={setCode}
          onRun={handleRun}
          loading={loading}
        />
        <ResultsPanel results={results} loading={loading} error={error} />
      </main>

      {/* Curtain — must be last child and sibling of input#dark-toggle */}
      <div className="curtain" aria-hidden="true" />
    </div>
  )
}

export default DashboardPage
