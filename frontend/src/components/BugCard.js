import { useState } from 'react'

/**
 * Collapsible card for a single AI-predicted bug.
 *
 * @param {Object} props
 * @param {Object} props.bug - A PredictedBug object from the backend.
 * @param {Function} props.onIgnore - Called when the ignore (✕) button is clicked.
 * @param {Function} [props.onHoverLine] - Called with the line number on mouseenter; null on mouseleave.
 */
function BugCard({ bug, onIgnore, onHoverLine }) {
  const [expanded, setExpanded] = useState(false)

  const cardClass = [
    'bug-card',
    `bug-sev-${bug.severity}`,
    bug.flagged ? 'flagged' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div
      className={cardClass}
      data-testid={`bug-${bug.bug_type}`}
      onMouseEnter={() => bug.line_number != null && onHoverLine?.({ line: bug.line_number, severity: bug.severity.toLowerCase() })}
      onMouseLeave={() => onHoverLine?.(null)}
    >
      <div className="bug-card-header">
        <span className={`severity-badge severity-${bug.severity}`}>
          {bug.severity}
        </span>
        <span className="bug-type" title={bug.bug_type}>{bug.bug_type}</span>
        {bug.line_number != null && (
          <span className="finding-line">L{bug.line_number}</span>
        )}
        {bug.confidence != null && (
          <span
            className={`confidence-badge${bug.flagged ? ' flagged' : ''}`}
            data-testid="confidence-badge"
            title={
              bug.flagged
                ? 'CodeBERT flagged this as likely false positive — excluded from score'
                : 'CodeBERT confidence that this is a real bug'
            }
          >
            {Math.round(bug.confidence * 100)}%
          </span>
        )}
        <button className="ignore-btn" onClick={onIgnore} title="Ignore this bug">
          ✕
        </button>
      </div>
      <p className="bug-description">{bug.description}</p>
      <button
        className="bug-fix-toggle"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
      >
        {expanded ? 'Hide fix' : 'Show suggested fix'}
      </button>
      {expanded && <pre className="bug-fix-code">{bug.suggested_fix}</pre>}
    </div>
  )
}

export default BugCard
