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
function BugCard({ bug, onIgnore, onHoverLine, onJumpLine, liveLine, codeSnippet }) {
  const [expanded, setExpanded] = useState(false)
  const [showCode, setShowCode] = useState(false)

  // liveLine === undefined => no tracking map yet, fall back to the original.
  // liveLine === null       => the flagged line was deleted — render as stale.
  // liveLine === number     => current position after edits.
  const effectiveLine = liveLine !== undefined ? liveLine : bug.line_number
  const isStale = liveLine === null
  const clickable = !isStale && effectiveLine != null
  const sev = bug.severity.toLowerCase()

  const cardClass = [
    'bug-card',
    `bug-sev-${bug.severity}`,
    clickable ? 'bug-clickable' : '',
    bug.flagged ? 'flagged' : '',
    isStale ? 'bug-card--stale' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div
      className={cardClass}
      data-testid={`bug-${bug.bug_type}`}
      onMouseEnter={() => clickable && onHoverLine?.({ line: effectiveLine, severity: sev })}
      onMouseLeave={() => onHoverLine?.(null)}
      onClick={() => clickable && onJumpLine?.({ line: effectiveLine, severity: sev })}
      onKeyDown={(e) => {
        if (!clickable) return
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onJumpLine?.({ line: effectiveLine, severity: sev })
        }
      }}
      role={clickable ? 'button' : undefined}
      tabIndex={clickable ? 0 : undefined}
      aria-label={clickable ? `Jump to line ${effectiveLine}` : undefined}
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
        {isStale ? (
          <span className="stale-badge" title="The flagged line was deleted">line deleted</span>
        ) : effectiveLine != null ? (
          <span className="finding-line">L{effectiveLine}</span>
        ) : null}
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
      <div className="bug-toggle-row">
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
        {codeSnippet && (
          <button
            className="bug-fix-toggle bug-show-code-toggle"
            onClick={(e) => {
              e.stopPropagation()
              setShowCode((prev) => !prev)
            }}
            aria-expanded={showCode}
          >
            {showCode ? 'Hide code' : 'Show code'}
          </button>
        )}
      </div>
      {expanded && <pre className="bug-fix-code">{bug.suggested_fix}</pre>}
      {showCode && codeSnippet && <pre className="bug-fix-code bug-code-snippet">{codeSnippet}</pre>}
    </div>
  )
}

export default BugCard
