import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { analyzeCode } from '../services/analysisService'
import CodeEditor from '../components/CodeEditor'
import ResultsPanel from '../components/ResultsPanel'
import '../styles/dashboard.css'

function DashboardPage() {
  const { user, session, signOut } = useAuth()
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  /**
   * Send the editor content to the backend and update the results panel.
   *
   * @param {string} code - Current editor content.
   */
  const handleRun = async (code) => {
    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const data = await analyzeCode(code, session.access_token)
      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="dashboard-page">
      <nav className="dashboard-nav">
        <span className="nav-title">CodePulse</span>
        <div className="nav-user">
          <span className="nav-email">{user?.email}</span>
          <button className="signout-btn" onClick={signOut}>
            Sign Out
          </button>
        </div>
      </nav>

      <main className="dashboard-main">
        <CodeEditor onRun={handleRun} loading={loading} />
        <ResultsPanel results={results} loading={loading} error={error} />
      </main>
    </div>
  )
}

export default DashboardPage
