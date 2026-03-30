import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/Toast'
import {
  getProfile,
  updateProfile,
  uploadAvatar,
  changePassword,
  deleteAccount,
} from '../services/accountService'
import TwoFactorSection from '../components/TwoFactorSection'
import '../styles/dashboard.css'
import '../styles/account.css'

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

function BackArrow() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="19" y1="12" x2="5" y2="12" />
      <polyline points="12 19 5 12 12 5" />
    </svg>
  )
}

function AccountPage() {
  const { session, signOut, refreshSession } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()
  const fileInputRef = useRef(null)
  const token = session?.access_token

  // Profile state
  const [profile, setProfile] = useState(null)
  const [pageLoading, setPageLoading] = useState(true)
  const [username, setUsername] = useState('')
  const [profileMsg, setProfileMsg] = useState(null)
  const [profileErr, setProfileErr] = useState(null)
  const [profileSaving, setProfileSaving] = useState(false)

  // Avatar state
  const [avatarPreview, setAvatarPreview] = useState(null)
  const [avatarFile, setAvatarFile] = useState(null)
  const [avatarMsg, setAvatarMsg] = useState(null)
  const [avatarErr, setAvatarErr] = useState(null)
  const [avatarSaving, setAvatarSaving] = useState(false)

  // Password state
  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [pwMsg, setPwMsg] = useState(null)
  const [pwErr, setPwErr] = useState(null)
  const [pwSaving, setPwSaving] = useState(false)

  // Delete state
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState('')
  const [deleteErr, setDeleteErr] = useState(null)
  const [deleting, setDeleting] = useState(false)

  // Load profile on mount
  useEffect(() => {
    if (!token) return
    getProfile(token)
      .then((data) => {
        setProfile(data)
        setUsername(data.username || '')
      })
      .catch(() => setProfileErr('Failed to load profile'))
      .finally(() => setPageLoading(false))
  }, [token])

  // ── Profile handlers ──
  const handleProfileSave = async (e) => {
    e.preventDefault()
    setProfileMsg(null)
    setProfileErr(null)

    if (username.length < 3 || username.length > 20) {
      setProfileErr('Username must be 3–20 characters')
      return
    }
    if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
      setProfileErr('Username may only contain letters, numbers, underscores, and hyphens')
      return
    }

    setProfileSaving(true)
    try {
      const updated = await updateProfile(token, { username })
      setProfile(updated)
      setProfileMsg('Profile updated')
      toast('Profile updated', 'success')
      await refreshSession()
    } catch (err) {
      setProfileErr(err.message)
      toast(err.message, 'error')
    } finally {
      setProfileSaving(false)
    }
  }

  // ── Avatar handlers ──
  const handleFileSelect = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setAvatarFile(file)
    setAvatarMsg(null)
    setAvatarErr(null)

    const reader = new FileReader()
    reader.onload = (ev) => setAvatarPreview(ev.target.result)
    reader.readAsDataURL(file)
  }

  const handleAvatarUpload = async () => {
    if (!avatarFile) return
    setAvatarMsg(null)
    setAvatarErr(null)
    setAvatarSaving(true)
    try {
      const result = await uploadAvatar(token, avatarFile)
      setProfile((p) => ({ ...p, profile_picture: result.profile_picture }))
      setAvatarFile(null)
      setAvatarPreview(null)
      setAvatarMsg('Profile picture updated')
      toast('Profile picture updated', 'success')
      await refreshSession()
    } catch (err) {
      setAvatarErr(err.message)
      toast(err.message, 'error')
    } finally {
      setAvatarSaving(false)
    }
  }

  // ── Password handlers ──
  const handlePasswordChange = async (e) => {
    e.preventDefault()
    setPwMsg(null)
    setPwErr(null)

    if (newPw.length < 8 || newPw.length > 128) {
      setPwErr('New password must be 8–128 characters')
      return
    }
    if (newPw !== confirmPw) {
      setPwErr('Passwords do not match')
      return
    }

    setPwSaving(true)
    try {
      await changePassword(token, {
        current_password: currentPw,
        new_password: newPw,
      })
      setPwMsg('Password changed successfully')
      toast('Password changed successfully', 'success')
      setCurrentPw('')
      setNewPw('')
      setConfirmPw('')
    } catch (err) {
      setPwErr(err.message)
      toast(err.message, 'error')
    } finally {
      setPwSaving(false)
    }
  }

  // ── Delete handlers ──
  const handleDelete = async () => {
    setDeleteErr(null)
    setDeleting(true)
    try {
      await deleteAccount(token)
      await signOut()
      navigate('/login')
    } catch (err) {
      setDeleteErr(err.message)
      setDeleting(false)
    }
  }

  const avatarColor = hashColor(profile?.id || '')
  const initial = profile?.username?.[0]?.toUpperCase() || '?'
  const displayAvatar = avatarPreview || profile?.profile_picture

  if (pageLoading) {
    return <div className="account-loading">Loading account...</div>
  }

  return (
    <div className="account-page">
      {/* ── Navbar ── */}
      <nav className="account-nav">
        <div className="account-nav-left">
          <button className="back-btn" onClick={() => navigate('/dashboard')}>
            <BackArrow /> Dashboard
          </button>
        </div>
        <span className="account-nav-title">Account Settings</span>
        <div style={{ width: 100 }} />
      </nav>

      <div className="account-content">
        {/* ── Profile Section ── */}
        <section className="account-section">
          <h2 className="account-section-title">Profile</h2>
          {profileMsg && <div className="account-success">{profileMsg}</div>}
          {profileErr && <div className="account-error">{profileErr}</div>}
          <form onSubmit={handleProfileSave}>
            <div className="account-field">
              <label className="account-label" htmlFor="account-email">Email</label>
              <input
                id="account-email"
                className="account-input account-input--readonly"
                type="email"
                value={profile?.email || ''}
                readOnly
              />
            </div>
            <div className="account-field">
              <label className="account-label" htmlFor="account-username">Username</label>
              <input
                id="account-username"
                className="account-input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                maxLength={20}
              />
            </div>
            <div className="account-field">
              <label className="account-label" htmlFor="account-role">Role</label>
              <input
                id="account-role"
                className="account-input account-input--readonly"
                type="text"
                value={profile?.role || 'developer'}
                readOnly
              />
            </div>
            <button
              type="submit"
              className="account-btn account-btn--primary"
              disabled={profileSaving || username === profile?.username}
            >
              {profileSaving ? 'Saving...' : 'Save Changes'}
            </button>
          </form>
        </section>

        {/* ── Avatar Section ── */}
        <section className="account-section">
          <h2 className="account-section-title">Profile Picture</h2>
          {avatarMsg && <div className="account-success">{avatarMsg}</div>}
          {avatarErr && <div className="account-error">{avatarErr}</div>}
          <div className="avatar-section">
            <div
              className="avatar-preview"
              style={!displayAvatar ? { background: avatarColor } : undefined}
            >
              {displayAvatar ? (
                <img src={displayAvatar} alt="avatar" />
              ) : (
                <span>{initial}</span>
              )}
            </div>
            <div className="avatar-actions">
              <input
                ref={fileInputRef}
                type="file"
                className="avatar-file-input"
                accept="image/png,image/jpeg,image/webp"
                onChange={handleFileSelect}
              />
              <button
                className="account-btn account-btn--outline"
                onClick={() => fileInputRef.current?.click()}
                type="button"
              >
                Choose Image
              </button>
              {avatarFile && (
                <button
                  className="account-btn account-btn--primary"
                  onClick={handleAvatarUpload}
                  disabled={avatarSaving}
                  type="button"
                >
                  {avatarSaving ? 'Uploading...' : 'Upload'}
                </button>
              )}
              <span className="avatar-hint">PNG, JPEG, or WebP. Max 2 MB.</span>
            </div>
          </div>
        </section>

        {/* ── Password Section ── */}
        <section className="account-section">
          <h2 className="account-section-title">Change Password</h2>
          {pwMsg && <div className="account-success">{pwMsg}</div>}
          {pwErr && <div className="account-error">{pwErr}</div>}
          <form onSubmit={handlePasswordChange}>
            <div className="account-field">
              <label className="account-label" htmlFor="current-password">Current Password</label>
              <input
                id="current-password"
                className="account-input"
                type="password"
                value={currentPw}
                onChange={(e) => setCurrentPw(e.target.value)}
                autoComplete="current-password"
              />
            </div>
            <div className="account-field">
              <label className="account-label" htmlFor="new-password">New Password</label>
              <input
                id="new-password"
                className="account-input"
                type="password"
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                placeholder="8–128 characters"
                autoComplete="new-password"
              />
            </div>
            <div className="account-field">
              <label className="account-label" htmlFor="confirm-password">Confirm New Password</label>
              <input
                id="confirm-password"
                className="account-input"
                type="password"
                value={confirmPw}
                onChange={(e) => setConfirmPw(e.target.value)}
                autoComplete="new-password"
              />
            </div>
            <button
              type="submit"
              className="account-btn account-btn--primary"
              disabled={pwSaving || !currentPw || !newPw || !confirmPw}
            >
              {pwSaving ? 'Changing...' : 'Change Password'}
            </button>
          </form>
        </section>

        {/* ── Security Section ── */}
        <TwoFactorSection />

        {/* ── Danger Zone ── */}
        <section className="account-section danger-zone">
          <h2 className="account-section-title">Danger Zone</h2>
          <p className="danger-description">
            Permanently delete your account and all associated data including submissions,
            analysis reports, and findings. This action cannot be undone.
          </p>
          <button
            className="account-btn account-btn--danger"
            onClick={() => setShowDeleteModal(true)}
            type="button"
          >
            Delete Account
          </button>
        </section>
      </div>

      {/* ── Delete Confirmation Modal ── */}
      {showDeleteModal && (
        <div className="modal-overlay" onClick={() => !deleting && setShowDeleteModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">Delete Account</h3>
            <p className="modal-text">
              This will permanently delete your account and all your data.
              Type <strong>{profile?.username}</strong> to confirm.
            </p>
            {deleteErr && <div className="account-error">{deleteErr}</div>}
            <div className="account-field">
              <input
                className="account-input"
                type="text"
                value={deleteConfirm}
                onChange={(e) => setDeleteConfirm(e.target.value)}
                placeholder="Type your username"
              />
            </div>
            <div className="modal-actions">
              <button
                className="account-btn account-btn--outline"
                onClick={() => setShowDeleteModal(false)}
                disabled={deleting}
                type="button"
              >
                Cancel
              </button>
              <button
                className="account-btn account-btn--danger"
                onClick={handleDelete}
                disabled={deleting || deleteConfirm !== profile?.username}
                type="button"
              >
                {deleting ? 'Deleting...' : 'Delete My Account'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AccountPage
