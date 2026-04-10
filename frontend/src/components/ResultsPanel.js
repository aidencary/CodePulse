import { useState, useMemo, useEffect, useRef, useCallback } from 'react'
import BugCard from './BugCard'
import { FINDING_SEV_RANK, BUG_SEV_RANK, scoreLevel } from '../utils/scoreHelpers'
import generateReportHTML from '../utils/generateReport'

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


// FR-REPORT-001
// FR-REPORT-002
// FR-REPORT-003
// FR-REPORT-004
// FR-REPORT-005
/**
 * SVG ring that fills like an arc based on score (0–100).
 * Renders as a circular track with a colored arc portion.
 */
function ScoreRing({ score, level, size = 88, strokeWidth = 4.5 }) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const filled = (score / 100) * circumference
  const gap = circumference - filled

  const colorMap = { good: '#4ade80', fair: '#facc15', poor: 'var(--danger)' }
  const color = colorMap[level] || 'var(--border)'

  return (
    <svg width={size} height={size} className="score-ring">
      {/* background track */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="var(--border)"
        strokeWidth={strokeWidth}
      />
      {/* filled arc */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeDasharray={`${filled} ${gap}`}
        strokeDashoffset={circumference / 4}
        strokeLinecap="round"
        style={{ transition: 'stroke-dasharray 0.6s ease' }}
      />
    </svg>
  )
}

function ResultsPanel({ results, loading, error, onHoverLine, submissionName }) {
  const [findingSort, setFindingSort] = useState('desc')
  const [findingSortField, setFindingSortField] = useState('severity')
  const [bugSort, setBugSort] = useState('desc')
  const [bugSortField, setBugSortField] = useState('severity')
  const [ignoredFindings, setIgnoredFindings] = useState(new Set())
  const [ignoredBugs, setIgnoredBugs] = useState(new Set())
  const [panelWidth, setPanelWidth] = useState(320)
  const isResizing = useRef(false)

  const handleMouseDown = useCallback((e) => {
    e.preventDefault()
    isResizing.current = true
    const startX = e.clientX
    const startWidth = panelWidth

    const onMouseMove = (ev) => {
      const delta = startX - ev.clientX
      setPanelWidth(Math.max(220, Math.min(600, startWidth + delta)))
    }
    const onMouseUp = () => {
      isResizing.current = false
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
    }
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
  }, [panelWidth])

  const handleDownloadReport = useCallback(() => {
    if (!results) return
    const html = generateReportHTML(results, submissionName)
    const blob = new Blob([html], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const safeName = (submissionName || 'report').replace(/[^a-z0-9_-]/gi, '_')
    a.download = `codepulse-report-${safeName}.html`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [results, submissionName])

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
            <div className="score-ring-wrapper">
              <ScoreRing
                score={results.overall_score}
                level={scoreLevel(results.overall_score)}
              />
              <div className="score-ring-text">
                <span className={`score-value score-value--${scoreLevel(results.overall_score)}`}>{results.overall_score}</span>
                <span className="score-label">/ 100</span>
              </div>
            </div>
            <p className="score-summary">{results.summary}</p>
          </div>

          {/* Static Analysis Findings */}
          {/* FR-REPORT-001 FR-REPORT-003 FR-REPORT-004 FR-REPORT-005 */}
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
                  className={`finding-item finding-sev-${f.severity.toLowerCase()}`}
                  data-testid={`finding-${f.issue_type}`}
                  onMouseEnter={() => f.line_number != null && onHoverLine?.({ line: f.line_number, severity: f.severity.toLowerCase() })}
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
          {/* FR-REPORT-002 FR-REPORT-003 FR-REPORT-004 FR-REPORT-005 */}
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
      <p className="results-placeholder">Add Python code and run analysis to see the results!</p>
    )
  }

  const totalIssues = results ? sortedFindings.length + sortedBugs.length : 0

  return (
    <div className="results-panel" style={{ width: panelWidth }}>
      <div className="resize-handle" onMouseDown={handleMouseDown} />
      <div className="panel-header">
        <h2 className="panel-title">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="panel-title-icon">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
          Results
          {results && <span className="panel-title-count">{totalIssues} {totalIssues === 1 ? 'issue' : 'issues'}</span>}
        </h2>
        {results && (
          <button className="download-report-btn" onClick={handleDownloadReport} title="Download HTML report">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Export
          </button>
        )}
      </div>
      <div className="results-body">
        {renderContent()}
      </div>
    </div>
  )
}

export default ResultsPanel
