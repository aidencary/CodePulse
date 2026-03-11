import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../context/AuthContext'

function ProfileDropdown({ user }) {
  const { signOut } = useAuth()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  const initial =
    user?.user_metadata?.username?.[0]?.toUpperCase() ||
    user?.email?.[0]?.toUpperCase() ||
    '?'

  const avatarUrl = user?.user_metadata?.avatar_url || null

  useEffect(() => {
    if (!open) return
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  return (
    <div className="profile-dropdown" ref={ref}>
      <button
        className="avatar-btn"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="true"
        aria-expanded={open}
        aria-label="Account menu"
      >
        {avatarUrl ? (
          <img src={avatarUrl} alt="avatar" className="avatar-img" />
        ) : (
          <span className="avatar-initial">{initial}</span>
        )}
      </button>

      {open && (
        <div className="dropdown-menu" role="menu">
          <button className="dropdown-item" role="menuitem" onClick={() => setOpen(false)}>
            Account
          </button>
          <button
            className="dropdown-item dropdown-item--danger"
            role="menuitem"
            onClick={() => { setOpen(false); signOut() }}
          >
            Sign Out
          </button>
        </div>
      )}
    </div>
  )
}

export default ProfileDropdown
