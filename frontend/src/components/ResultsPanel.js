import { useState, useMemo, useEffect } from 'react'
import BugCard from './BugCard'

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


function ResultsPanel({ results, loading, error, onHoverLine }) {
  const [findingSort, setFindingSort] = useState('desc')
  const [findingSortField, setFindingSortField] = useState('severity')
  const [bugSort, setBugSort] = useState('desc')
  const [bugSortField, setBugSortField] = useState('severity')
  const [ignoredFindings, setIgnoredFindings] = useState(new Set())
  const [ignoredBugs, setIgnoredBugs] = useState(new Set())

  // Reset sort and ignore state when a new submission is loaded
  useEffect(() => {
    setFindingSort('desc')
    setFindingSortField('severity')
    setBugSort('desc')
    setBugSortField('severity')
    setIgnoredFindings(new Set())
    setIgnoredBugs(new Set())
  }, [results])

  const findingKey = (f) => `${f.issue_type}|${f.line_number}|${f.message}`
  const bugKey = (b) => `${b.bug_type}|${b.line_number}`

  const scoreLevel = (score) => {
    if (score >= 80) return 'good'
    if (score >= 50) return 'fair'
    return 'poor'
  }

  const visibleFindings = useMemo(() => {
    return (results?.findings || []).filter((f) => !ignoredFindings.has(findingKey(f)))
  }, [results?.findings, ignoredFindings]) // eslint-disable-line react-hooks/exhaustive-deps

  const visibleBugs = useMemo(() => {
    return (results?.predicted_bugs || []).filter((b) => !ignoredBugs.has(bugKey(b)))
  }, [results?.predicted_bugs, ignoredBugs]) // eslint-disable-line react-hooks/exhaustive-deps

  const sortedFindings = useMemo(() => {
    const findings = visibleFindings
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
  }, [visibleFindings, findingSort, findingSortField])

  const sortedBugs = useMemo(() => {
    const bugs = visibleBugs
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
  }, [visibleBugs, bugSort, bugSortField])

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
              sortedFindings.map((f) => (
                <div
                  key={findingKey(f)}
                  className="finding-item"
                  onMouseEnter={() => f.line_number != null && onHoverLine?.(f.line_number)}
                  onMouseLeave={() => onHoverLine?.(null)}
                >
                  <span
                    className={`severity-badge severity-${f.severity.toLowerCase()}`}
                  >
                    {f.severity}
                  </span>
                  <span className="finding-type">{f.issue_type}</span>
                  {f.line_number != null && (
                    <span className="finding-line">L{f.line_number}</span>
                  )}
                  <button
                    className="ignore-btn"
                    onClick={() => setIgnoredFindings((prev) => new Set([...prev, findingKey(f)]))}
                    title="Ignore this finding"
                  >✕</button>
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
              sortedBugs.map((bug) => (
                <BugCard
                  key={bugKey(bug)}
                  bug={bug}
                  onIgnore={() => setIgnoredBugs((prev) => new Set([...prev, bugKey(bug)]))}
                  onHoverLine={onHoverLine}
                />
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
