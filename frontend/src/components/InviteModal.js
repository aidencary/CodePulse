import { useRef, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { inviteUser } from '../services/accountService'
import { useToast } from './Toast'

function InviteModal({ onClose }) {
  const { session } = useAuth()
  const toast = useToast()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  // FR-ACCT-005
  // FR-DASH-005
  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await inviteUser(session.access_token, email.trim())
      toast(`Invite sent to ${email.trim()}`, 'success')
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleBackdrop = (e) => {
    if (e.target === e.currentTarget) onClose()
  }

  return (
    <div className="invite-backdrop" onClick={handleBackdrop}>
      <div className="invite-modal" role="dialog" aria-modal="true" aria-labelledby="invite-title">
        <h2 className="invite-title" id="invite-title">Invite a User</h2>
        <p className="invite-hint">
          They'll receive an email with a link to set up their CodePulse account.
        </p>
        <form onSubmit={handleSubmit}>
          <label className="invite-label" htmlFor="invite-email">Email address</label>
          <input
            ref={inputRef}
            id="invite-email"
            className="invite-input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="user@example.com"
            autoFocus
            required
          />
          {error && <div className="invite-error">{error}</div>}
          <div className="invite-actions">
            <button type="button" className="invite-btn invite-btn--cancel" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="invite-btn invite-btn--send"
              disabled={loading || !email.trim()}
            >
              {loading ? 'Sending…' : 'Send Invite'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default InviteModal
