import { forwardRef, useEffect, useImperativeHandle, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { getSubmissions, renameSubmission, deleteSubmission } from '../services/submissionService'
import { useToast } from './Toast'

const SIDEBAR_ICON = (
  <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
    <path d="M1 3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V3zm5 0v10h8V3H6zM2 3v10h3V3H2z" />
  </svg>
)

const TRASH_ICON = (
  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" aria-hidden="true">
    <path d="M2 4h12M5.33 4V2.67a1.33 1.33 0 0 1 1.34-1.34h2.66a1.33 1.33 0 0 1 1.34 1.34V4m2 0v9.33a1.33 1.33 0 0 1-1.34 1.34H4.67a1.33 1.33 0 0 1-1.34-1.34V4h9.34z" />
  </svg>
)

function getTitle(submission) {
  if (submission.name) return submission.name
  const first = (submission.code || '').trim().split('\n').find((l) => l.trim()) || 'Untitled'
  return first.length > 32 ? first.slice(0, 32) + '\u2026' : first
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

const SubmissionSidebar = forwardRef(function SubmissionSidebar(
  { onSelect, activeId, onClose, onOpen, open },
  ref
) {
  const { user, session } = useAuth()
  const toast = useToast()
  const [submissions, setSubmissions] = useState([])
  const [search, setSearch] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editValue, setEditValue] = useState('')
  const [deletingId, setDeletingId] = useState(null)

  const token = session?.access_token

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

  const handleRenameStart = (e, s) => {
    e.stopPropagation()
    setEditingId(s.submission_id)
    setEditValue(s.name || '')
  }

  const handleRenameSubmit = async (submissionId) => {
    if (!editValue.trim()) {
      setEditingId(null)
      return
    }
    try {
      await renameSubmission(submissionId, editValue.trim(), token)
      toast('Submission renamed', 'success')
      await load()
    } catch {
      toast('Failed to rename submission', 'error')
    }
    setEditingId(null)
  }

  const handleRenameKey = (e, submissionId) => {
    if (e.key === 'Enter') handleRenameSubmit(submissionId)
    if (e.key === 'Escape') setEditingId(null)
  }

  const handleDeleteClick = (e, submissionId) => {
    e.stopPropagation()
    setDeletingId(submissionId)
  }

  const handleDeleteConfirm = async () => {
    try {
      await deleteSubmission(deletingId, token)
      toast('Submission deleted', 'success')
      if (activeId === deletingId) onSelect(null)
      await load()
    } catch {
      toast('Failed to delete submission', 'error')
    }
    setDeletingId(null)
  }

  const filtered = submissions.filter((s) =>
    getTitle(s).toLowerCase().includes(search.toLowerCase())
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
          placeholder="Search\u2026"
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
            <div className="submission-item-row">
              {editingId === s.submission_id ? (
                <input
                  className="submission-rename-input"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onBlur={() => handleRenameSubmit(s.submission_id)}
                  onKeyDown={(e) => handleRenameKey(e, s.submission_id)}
                  onClick={(e) => e.stopPropagation()}
                  autoFocus
                  maxLength={100}
                />
              ) : (
                <span
                  className="submission-title"
                  onDoubleClick={(e) => handleRenameStart(e, s)}
                  title="Double-click to rename"
                >
                  {getTitle(s)}
                </span>
              )}
              <button
                className="submission-delete-btn"
                onClick={(e) => handleDeleteClick(e, s.submission_id)}
                title="Delete submission"
                aria-label="Delete submission"
              >
                {TRASH_ICON}
              </button>
            </div>
            <span className="submission-date">{formatDate(s.created_at)}</span>
          </li>
        ))}
      </ul>

      {/* Delete confirmation modal */}
      {deletingId && (
        <div className="sidebar-delete-modal">
          <p>Delete this submission?</p>
          <div className="sidebar-delete-actions">
            <button className="sidebar-delete-cancel" onClick={() => setDeletingId(null)}>Cancel</button>
            <button className="sidebar-delete-confirm" onClick={handleDeleteConfirm}>Delete</button>
          </div>
        </div>
      )}
    </aside>
  )
})

export default SubmissionSidebar
