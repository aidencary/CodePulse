import { forwardRef, useEffect, useImperativeHandle, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { getSubmissions } from '../services/submissionService'

function getTitle(code) {
  const first = (code || '').trim().split('\n').find((l) => l.trim()) || 'Untitled'
  return first.length > 32 ? first.slice(0, 32) + '…' : first
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

const SubmissionSidebar = forwardRef(function SubmissionSidebar({ onSelect, activeId }, ref) {
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

  return (
    <aside className="submission-sidebar">
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
