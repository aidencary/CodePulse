import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import supabase from '../services/supabaseClient'
import { useToast } from '../components/Toast'
import '../styles/auth.css'

function ResetPasswordPage() {
  const [ready, setReady] = useState(false)
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()
  const toast = useToast()

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'PASSWORD_RECOVERY') setReady(true)
    })
    return () => subscription.unsubscribe()
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setSubmitting(true)
    const { error: updateError } = await supabase.auth.updateUser({ password })
    setSubmitting(false)
    if (updateError) {
      setError(updateError.message)
      return
    }
    toast('Password updated! Please log in.', 'success')
    navigate('/login')
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-title">CodePulse</h1>
        {!ready ? (
          <p className="auth-loading">Processing reset link&hellip;</p>
        ) : (
          <form onSubmit={handleSubmit} className="auth-form" aria-label="reset password">
            <div className="form-group">
              <label htmlFor="new-password">New Password</label>
              <input
                id="new-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
                minLength={8}
                maxLength={128}
                placeholder="••••••••"
              />
            </div>
            <div className="form-group">
              <label htmlFor="confirm-password">Confirm Password</label>
              <input
                id="confirm-password"
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                autoComplete="new-password"
                minLength={8}
                maxLength={128}
                placeholder="••••••••"
              />
            </div>
            {error && <p className="auth-error">{error}</p>}
            <button type="submit" className="auth-submit" disabled={submitting}>
              {submitting ? 'Please wait...' : 'Update Password'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

export default ResetPasswordPage
