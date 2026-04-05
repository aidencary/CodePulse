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

  return (
    <div
      className={`bug-card bug-sev-${bug.severity}`}
      data-testid={`bug-${bug.bug_type}`}
      onMouseEnter={() => bug.line_number != null && onHoverLine?.(bug.line_number)}
      onMouseLeave={() => onHoverLine?.(null)}
    >
      <div className="bug-card-header">
        <span className={`severity-badge severity-${bug.severity}`}>
          {bug.severity}
        </span>
        <span className="bug-type">{bug.bug_type}</span>
        {bug.line_number != null && (
          <span className="finding-line">L{bug.line_number}</span>
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
