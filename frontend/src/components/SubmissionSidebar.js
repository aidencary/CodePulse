import { forwardRef, useEffect, useImperativeHandle, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { getSubmissions } from '../services/submissionService'

const SIDEBAR_ICON = (
  <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
    <path d="M1 3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V3zm5 0v10h8V3H6zM2 3v10h3V3H2z" />
  </svg>
)

function getTitle(code) {
  const first = (code || '').trim().split('\n').find((l) => l.trim()) || 'Untitled'
  return first.length > 32 ? first.slice(0, 32) + '…' : first
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

const SubmissionSidebar = forwardRef(function SubmissionSidebar(
  { onSelect, activeId, onClose, onOpen, open },
  ref
) {
  const { user } = useAuth()
  const [submissions, setSubmissions] = useState([])
  const [search, setSearch] = useState('')

  const load = async () => {
    if (!user) return
    try {
      const data = await getSubmissions(user.id)
      setSubmissions(data)
    } catch {
      // silently fail — sidebar is non-critical
    }
  }

  useEffect(() => { load() }, [user]) // eslint-disable-line react-hooks/exhaustive-deps

  useImperativeHandle(ref, () => ({ refresh: load }))

  const filtered = submissions.filter((s) =>
    getTitle(s.code).toLowerCase().includes(search.toLowerCase())
  )

  if (!open) {
    return (
      <aside className="submission-sidebar sidebar-collapsed">
        <button
          className="sidebar-logo-btn sidebar-logo-crossfade"
          onClick={onOpen}
          aria-label="Open submissions"
          title="Open submissions"
        >
          <img src="/favicon.png" className="sidebar-logo-img" alt="" aria-hidden="true" />
          <span className="sidebar-toggle-icon">{SIDEBAR_ICON}</span>
        </button>
        <button
          className="new-btn"
          onClick={() => { onOpen(); onSelect(null) }}
          title="New submission"
        >
          +
        </button>
      </aside>
    )
  }

  return (
    <aside className="submission-sidebar">
      <div className="sidebar-top">
        <button
          className="sidebar-logo-btn sidebar-logo-home"
          onClick={() => onSelect(null)}
          aria-label="New submission"
          title="New submission"
        >
          <img src="/favicon.png" className="sidebar-logo-img" alt="" aria-hidden="true" />
        </button>
        <button
          className="sidebar-close-icon-btn"
          onClick={onClose}
          aria-label="Close submissions"
          title="Close submissions"
        >
          {SIDEBAR_ICON}
        </button>
      </div>

      <div className="sidebar-header">
        <span className="sidebar-title">Submissions</span>
        <button className="new-btn" onClick={() => onSelect(null)} title="New submission">
          +
        </button>
      </div>

      <div className="sidebar-search">
        <input
          type="search"
          placeholder="Search…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="search-input"
        />
      </div>

      <ul className="submission-list">
        {filtered.length === 0 && (
          <li className="submission-empty">No submissions yet</li>
        )}
        {filtered.map((s) => (
          <li
            key={s.submission_id}
            className={`submission-item${s.submission_id === activeId ? ' active' : ''}`}
            onClick={() => onSelect(s)}
          >
            <span className="submission-title">{getTitle(s.code)}</span>
            <span className="submission-date">{formatDate(s.created_at)}</span>
          </li>
        ))}
      </ul>
    </aside>
  )
})

export default SubmissionSidebar
