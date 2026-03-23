import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const AVATAR_PALETTE = [
  '#e74c3c', '#e67e22', '#16a34a', '#0891b2',
  '#7c3aed', '#db2777', '#d97706', '#2563eb',
  '#059669', '#9333ea', '#dc2626', '#0284c7',
]

function hashColor(str = '') {
  let h = 0
  for (let i = 0; i < str.length; i++) h = str.charCodeAt(i) + ((h << 5) - h)
  return AVATAR_PALETTE[Math.abs(h) % AVATAR_PALETTE.length]
}

function ProfileDropdown({ user }) {
  const { signOut } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  const initial =
    user?.user_metadata?.username?.[0]?.toUpperCase() ||
    user?.email?.[0]?.toUpperCase() ||
    '?'

  const rawAvatarUrl = user?.user_metadata?.avatar_url || null
  const avatarUrl = (() => {
    if (!rawAvatarUrl) return null
    try {
      const { protocol, hostname } = new URL(rawAvatarUrl)
      const allowedHosts = ['lh3.googleusercontent.com', 'avatars.githubusercontent.com', 's.gravatar.com']
      return protocol === 'https:' && allowedHosts.includes(hostname) ? rawAvatarUrl : null
    } catch {
      return null
    }
  })()
  const avatarColor = hashColor(user?.id || user?.email || '')

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
        style={!avatarUrl ? { background: avatarColor } : undefined}
      >
        {avatarUrl ? (
          <img src={avatarUrl} alt="avatar" className="avatar-img" />
        ) : (
          <span className="avatar-initial">{initial}</span>
        )}
      </button>

      {open && (
        <div className="dropdown-menu" role="menu">
          <button className="dropdown-item" role="menuitem" onClick={() => { setOpen(false); navigate('/account') }}>
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
