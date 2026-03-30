/**
 * Results panel that displays the structured analysis output from the backend.
 *
 * @param {Object} props
 * @param {Object|null} props.results - Parsed JSON response from the backend.
 * @param {boolean} props.loading - True while the API request is in flight.
 * @param {string|null} props.error - Error message to display on failure.
 */
import { useState, useMemo, useEffect } from 'react'

/** Severity rank maps (higher number = more severe). */
const FINDING_SEV_RANK = { high: 3, med: 2, low: 1 }
const BUG_SEV_RANK = { critical: 4, high: 3, medium: 2, low: 1 }

/**
 * Inline sort controls: "Severity" and "Line" field-selector pills plus a direction toggle.
 *
 * @param {'severity'|'line'} field - The active primary sort field.
 * @param {'asc'|'desc'} direction - Current sort direction.
 * @param {Function} onFieldChange - Called with the new field when a pill is clicked.
 * @param {Function} onDirectionToggle - Called when the ↑/↓ button is clicked.
 */
function SortControls({ field, direction, onFieldChange, onDirectionToggle }) {
  return (
    <div className="sort-controls">
      <button
        className={`sort-pill${field === 'severity' ? ' sort-pill--active' : ''}`}
        onClick={() => onFieldChange('severity')}
        aria-pressed={field === 'severity'}
      >
        Severity
      </button>
      <button
        className={`sort-pill${field === 'line' ? ' sort-pill--active' : ''}`}
        onClick={() => onFieldChange('line')}
        aria-pressed={field === 'line'}
      >
        Line
      </button>
      <button
        className="sort-toggle"
        onClick={onDirectionToggle}
        title={direction === 'desc' ? 'Sorted high → low' : 'Sorted low → high'}
        aria-label={`Sort ${direction === 'asc' ? 'low to high' : 'high to low'}`}
      >
        {direction === 'desc' ? '↓' : '↑'}
      </button>
    </div>
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
  const [findingSortField, setFindingSortField] = useState('severity')
  const [bugSort, setBugSort] = useState('desc')
  const [bugSortField, setBugSortField] = useState('severity')

  // Reset sort state when a new submission is loaded
  useEffect(() => {
    setFindingSort('desc')
    setFindingSortField('severity')
    setBugSort('desc')
    setBugSortField('severity')
  }, [results])

  const scoreLevel = (score) => {
    if (score >= 80) return 'good'
    if (score >= 50) return 'fair'
    return 'poor'
  }

  const sortedFindings = useMemo(() => {
    const findings = results?.findings || []
    const dir = findingSort === 'desc' ? -1 : 1
    return [...findings].sort((a, b) => {
      if (findingSortField === 'severity') {
        const diff =
          (FINDING_SEV_RANK[a.severity.toLowerCase()] || 0) -
          (FINDING_SEV_RANK[b.severity.toLowerCase()] || 0)
        if (diff !== 0) return dir * diff
        // tiebreaker: line number ascending, nulls last
        if (a.line_number == null && b.line_number == null) return 0
        if (a.line_number == null) return 1
        if (b.line_number == null) return -1
        return a.line_number - b.line_number
      } else {
        // primary: line number, nulls last
        if (a.line_number == null && b.line_number == null) return 0
        if (a.line_number == null) return 1
        if (b.line_number == null) return -1
        const diff = a.line_number - b.line_number
        if (diff !== 0) return dir * diff
        // tiebreaker: severity descending
        return (
          (FINDING_SEV_RANK[b.severity.toLowerCase()] || 0) -
          (FINDING_SEV_RANK[a.severity.toLowerCase()] || 0)
        )
      }
    })
  }, [results?.findings, findingSort, findingSortField])

  const sortedBugs = useMemo(() => {
    const bugs = results?.predicted_bugs || []
    const dir = bugSort === 'desc' ? -1 : 1
    return [...bugs].sort((a, b) => {
      if (bugSortField === 'severity') {
        const diff =
          (BUG_SEV_RANK[a.severity.toLowerCase()] || 0) -
          (BUG_SEV_RANK[b.severity.toLowerCase()] || 0)
        if (diff !== 0) return dir * diff
        // tiebreaker: line number ascending, nulls last
        if (a.line_number == null && b.line_number == null) return 0
        if (a.line_number == null) return 1
        if (b.line_number == null) return -1
        return a.line_number - b.line_number
      } else {
        // primary: line number, nulls last
        if (a.line_number == null && b.line_number == null) return 0
        if (a.line_number == null) return 1
        if (b.line_number == null) return -1
        const diff = a.line_number - b.line_number
        if (diff !== 0) return dir * diff
        // tiebreaker: severity descending
        return (
          (BUG_SEV_RANK[b.severity.toLowerCase()] || 0) -
          (BUG_SEV_RANK[a.severity.toLowerCase()] || 0)
        )
      }
    })
  }, [results?.predicted_bugs, bugSort, bugSortField])

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
                <SortControls
                  field={findingSortField}
                  direction={findingSort}
                  onFieldChange={(f) => { setFindingSortField(f); setFindingSort(f === 'line' ? 'asc' : 'desc') }}
                  onDirectionToggle={() => setFindingSort((d) => d === 'desc' ? 'asc' : 'desc')}
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
                <SortControls
                  field={bugSortField}
                  direction={bugSort}
                  onFieldChange={(f) => { setBugSortField(f); setBugSort(f === 'line' ? 'asc' : 'desc') }}
                  onDirectionToggle={() => setBugSort((d) => d === 'desc' ? 'asc' : 'desc')}
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
