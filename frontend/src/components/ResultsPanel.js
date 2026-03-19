/**
 * Results panel that displays the structured analysis output from the backend.
 *
 * @param {Object} props
 * @param {Object|null} props.results - Parsed JSON response from the backend.
 * @param {boolean} props.loading - True while the API request is in flight.
 * @param {string|null} props.error - Error message to display on failure.
 */
import { useState } from 'react'

/**
 * Collapsible card for a single AI-predicted bug.
 *
 * @param {Object} props
 * @param {Object} props.bug - A PredictedBug object from the backend.
 */
function BugCard({ bug }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={`bug-card bug-sev-${bug.severity}`}>
      <div className="bug-card-header">
        <span className={`severity-badge severity-${bug.severity}`}>
          {bug.severity}
        </span>
        <span className="bug-type">{bug.bug_type}</span>
        {bug.line_number != null && (
          <span className="finding-line">L{bug.line_number}</span>
        )}
      </div>
      <p className="bug-description">{bug.description}</p>
      <button
        className="bug-fix-toggle"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
      >
        {expanded ? 'Hide fix' : 'Show suggested fix'}
      </button>
      {expanded && (
        <pre className="bug-fix-code">{bug.suggested_fix}</pre>
      )}
    </div>
  )
}

function ResultsPanel({ results, loading, error }) {
  const scoreLevel = (score) => {
    if (score >= 80) return 'good'
    if (score >= 50) return 'fair'
    return 'poor'
  }

  const renderContent = () => {
    if (loading) {
      return (
        <div className="results-skeleton" aria-label="Analyzing…">
          <div className="skeleton-score" />
          <div className="skeleton-line" />
          <div className="skeleton-line skeleton-line--short" />
          <div className="skeleton-line" />
        </div>
      )
    }
    if (error) {
      return <p className="results-error">{error}</p>
    }
    if (results) {
      return (
        <>
          {/* Score */}
          <div className="score-section">
            <div
              className="score-circle"
              data-level={scoreLevel(results.overall_score)}
            >
              <span className="score-value">{results.overall_score}</span>
              <span className="score-label">/ 100</span>
            </div>
            <p className="score-summary">{results.summary}</p>
          </div>

          {/* Static Analysis Findings */}
          <section className="results-section">
            <h3 className="section-title">
              Static Analysis{' '}
              <span className="badge">{results.findings.length}</span>
            </h3>
            {results.findings.length === 0 ? (
              <p className="results-placeholder">No issues found.</p>
            ) : (
              results.findings.map((f, i) => (
                <div key={i} className="finding-item">
                  <span
                    className={`severity-badge severity-${f.severity.toLowerCase()}`}
                  >
                    {f.severity}
                  </span>
                  <span className="finding-type">{f.issue_type}</span>
                  {f.line_number != null && (
                    <span className="finding-line">L{f.line_number}</span>
                  )}
                  <p className="finding-message">{f.message}</p>
                </div>
              ))
            )}
          </section>

          {/* AI Bug Predictions */}
          <section className="results-section">
            <h3 className="section-title">
              AI Bug Predictions{' '}
              <span className="badge">{results.predicted_bugs.length}</span>
            </h3>
            {results.predicted_bugs.length === 0 ? (
              <p className="results-placeholder">No predicted bugs found.</p>
            ) : (
              results.predicted_bugs.map((bug, i) => (
                <BugCard key={i} bug={bug} />
              ))
            )}
          </section>
        </>
      )
    }
    return (
      <p className="results-placeholder">Run analysis to see results.</p>
    )
  }

  return (
    <div className="results-panel">
      <div className="panel-header">
        <h2 className="panel-title">Results</h2>
      </div>
      <div className="results-body">
        {renderContent()}
      </div>
    </div>
  )
}

export default ResultsPanel
