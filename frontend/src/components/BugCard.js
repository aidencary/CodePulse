import { useState } from 'react'

/**
 * Collapsible card for a single AI-predicted bug.
 *
 * @param {Object} props
 * @param {Object} props.bug - A PredictedBug object from the backend.
 * @param {Function} props.onIgnore - Called when the ignore (✕) button is clicked.
 * @param {Function} [props.onHoverLine] - Called with the line number on mouseenter; null on mouseleave.
 * @param {Function} [props.onJumpLine] - Called with line/severity when the card is clicked.
 */
function BugCard({ bug, onIgnore, onHoverLine, onJumpLine }) {
  const [expanded, setExpanded] = useState(false)

  const cardClass = [
    'bug-card',
    `bug-sev-${bug.severity}`,
    bug.line_number != null ? 'bug-clickable' : '',
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
      onClick={() => bug.line_number != null && onJumpLine?.({ line: bug.line_number, severity: bug.severity.toLowerCase() })}
      onKeyDown={(e) => {
        if (bug.line_number == null) return
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onJumpLine?.({ line: bug.line_number, severity: bug.severity.toLowerCase() })
        }
      }}
      role={bug.line_number != null ? 'button' : undefined}
      tabIndex={bug.line_number != null ? 0 : undefined}
      aria-label={bug.line_number != null ? `Jump to line ${bug.line_number}` : undefined}
    >
      <div className="bug-card-header">
        {bug.flagged && (
          <span
            className="bug-flag-icon"
            title="CodeBERT flagged this as a likely false positive — excluded from score"
            aria-label="Flagged as likely false positive"
          >
            <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M5 3a1 1 0 0 1 1 1v16a1 1 0 1 1-2 0V4a1 1 0 0 1 1-1zm2 1h11.382a1 1 0 0 1 .894 1.447L17.618 9l1.658 3.553A1 1 0 0 1 18.382 14H7V4z" />
            </svg>
          </span>
        )}
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
        <button
          className="ignore-btn"
          onClick={(e) => {
            e.stopPropagation()
            onIgnore()
          }}
          title="Ignore this bug"
        >
          ✕
        </button>
      </div>
      <p className="bug-description">{bug.description}</p>
      <button
        className="bug-fix-toggle"
        onClick={(e) => {
          e.stopPropagation()
          setExpanded((prev) => !prev)
        }}
        aria-expanded={expanded}
      >
        {expanded ? 'Hide fix' : 'Show suggested fix'}
      </button>
      {expanded && <pre className="bug-fix-code">{bug.suggested_fix}</pre>}
    </div>
  )
}

export default BugCard
