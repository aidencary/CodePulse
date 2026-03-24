/**
 * Results panel that displays the structured analysis output from the backend.
 *
 * @param {Object} props
 * @param {Object|null} props.results - Parsed JSON response from the backend.
 * @param {boolean} props.loading - True while the API request is in flight.
 * @param {string|null} props.error - Error message to display on failure.
 */
import { useState, useMemo } from 'react'

/** Severity rank maps (higher number = more severe). */
const FINDING_SEV_RANK = { high: 3, med: 2, low: 1 }
const BUG_SEV_RANK = { critical: 4, high: 3, medium: 2, low: 1 }

/**
 * Small sort-direction toggle shown next to a section title.
 */
function SortToggle({ direction, onToggle }) {
  return (
    <button
      className="sort-toggle"
      onClick={onToggle}
      title={direction === 'desc' ? 'Sorted high → low' : 'Sorted low → high'}
      aria-label={`Sort severity ${direction === 'desc' ? 'low to high' : 'high to low'}`}
    >
      {direction === 'desc' ? '↓' : '↑'}
    </button>
  )
}

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
  const [findingSort, setFindingSort] = useState('desc')
  const [bugSort, setBugSort] = useState('desc')

  const scoreLevel = (score) => {
    if (score >= 80) return 'good'
    if (score >= 50) return 'fair'
    return 'poor'
  }

  const sortedFindings = useMemo(() => {
    const findings = results?.findings || []
    const multiplier = findingSort === 'desc' ? -1 : 1
    return [...findings].sort((a, b) => {
      const aRank = FINDING_SEV_RANK[a.severity.toLowerCase()] || 0
      const bRank = FINDING_SEV_RANK[b.severity.toLowerCase()] || 0
      return multiplier * (aRank - bRank)
    })
  }, [results?.findings, findingSort])

  const sortedBugs = useMemo(() => {
    const bugs = results?.predicted_bugs || []
    const multiplier = bugSort === 'desc' ? -1 : 1
    return [...bugs].sort((a, b) => {
      const aRank = BUG_SEV_RANK[a.severity.toLowerCase()] || 0
      const bRank = BUG_SEV_RANK[b.severity.toLowerCase()] || 0
      return multiplier * (aRank - bRank)
    })
  }, [results?.predicted_bugs, bugSort])

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
              <span className="badge">{sortedFindings.length}</span>
              {sortedFindings.length > 1 && (
                <SortToggle
                  direction={findingSort}
                  onToggle={() => setFindingSort((d) => d === 'desc' ? 'asc' : 'desc')}
                />
              )}
            </h3>
            {sortedFindings.length === 0 ? (
              <p className="results-placeholder">No issues found.</p>
            ) : (
              sortedFindings.map((f, i) => (
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
              <span className="badge">{sortedBugs.length}</span>
              {sortedBugs.length > 1 && (
                <SortToggle
                  direction={bugSort}
                  onToggle={() => setBugSort((d) => d === 'desc' ? 'asc' : 'desc')}
                />
              )}
            </h3>
            {sortedBugs.length === 0 ? (
              <p className="results-placeholder">No predicted bugs found.</p>
            ) : (
              sortedBugs.map((bug, i) => (
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
