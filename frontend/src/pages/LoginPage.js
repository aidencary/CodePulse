import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import supabase from '../services/supabaseClient'
import '../styles/auth.css'

function LoginPage() {
  const [mode, setMode] = useState('login') // 'login' | 'signup' | 'forgot'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [loginFailed, setLoginFailed] = useState(false)
  const [step, setStep] = useState('credentials') // 'credentials' | 'mfa'
  const [mfaFactorId, setMfaFactorId] = useState(null)
  const [mfaCode, setMfaCode] = useState('')

  const { signIn, signUp } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setSubmitting(true)

    if (step === 'mfa') {
      const { data: challenge, error: cErr } = await supabase.auth.mfa.challenge({
        factorId: mfaFactorId,
      })
      if (cErr) {
        setError(cErr.message)
        setSubmitting(false)
        return
      }
      const { error: vErr } = await supabase.auth.mfa.verify({
        factorId: mfaFactorId,
        challengeId: challenge.id,
        code: mfaCode.trim(),
      })
      setSubmitting(false)
      if (vErr) {
        setError('Invalid code — please try again')
        return
      }
      navigate('/dashboard')
      return
    }

    if (mode === 'forgot') {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      })
      setSubmitting(false)
      if (error) {
        setError(error.message)
      } else {
        setSuccess('Check your email for a password reset link.')
        setEmail('')
      }
      return
    }

    const { error } = mode === 'login'
      ? await signIn(email, password)
      : await signUp(email, password, username)

    if (error) {
      setSubmitting(false)
      setError(error.message)
      if (mode === 'login') setLoginFailed(true)
      return
    }

    if (mode === 'login') {
      // Check if MFA step-up is required
      const { data: aalData } = await supabase.auth.mfa.getAuthenticatorAssuranceLevel()
      if (aalData?.nextLevel === 'aal2' && aalData?.currentLevel !== 'aal2') {
        const { data: factors } = await supabase.auth.mfa.listFactors()
        const totp = factors?.totp?.find((f) => f.status === 'verified')
        if (totp) {
          setMfaFactorId(totp.id)
          setStep('mfa')
          setSubmitting(false)
          return
        }
      }
      setSubmitting(false)
      navigate('/dashboard')
    } else {
      setSubmitting(false)
      setSuccess('Account created! Check your email to confirm before logging in.')
    }
  }

  const switchMode = (newMode) => {
    setMode(newMode)
    setError(null)
    setSuccess(null)
    setLoginFailed(false)
  }

  const handleMfaBack = async () => {
    await supabase.auth.signOut()
    setStep('credentials')
    setMfaFactorId(null)
    setMfaCode('')
    setError(null)
  }

  if (step === 'mfa') {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <h1 className="auth-title">CodePulse</h1>
          <p className="auth-mfa-hint">
            Enter the 6-digit code from your authenticator app.
          </p>
          <form onSubmit={handleSubmit} className="auth-form" aria-label="two-factor authentication">
            <div className="form-group">
              <label htmlFor="mfa-code">Authentication Code</label>
              <input
                id="mfa-code"
                type="text"
                inputMode="numeric"
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value)}
                required
                maxLength={6}
                placeholder="000000"
                autoComplete="one-time-code"
                autoFocus
              />
            </div>
            {error && <p className="auth-error">{error}</p>}
            <button type="submit" className="auth-submit" disabled={submitting}>
              {submitting ? 'Please wait...' : 'Verify'}
            </button>
            <button type="button" className="auth-link" onClick={handleMfaBack}>
              Back to Log In
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-title">CodePulse</h1>

        {mode !== 'forgot' && (
          <div className="auth-toggle">
            <button
              className={mode === 'login' ? 'active' : ''}
              onClick={() => switchMode('login')}
            >
              Log In
            </button>
            <button
              className={mode === 'signup' ? 'active' : ''}
              onClick={() => switchMode('signup')}
            >
              Sign Up
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form" aria-label="authentication">
          {mode === 'signup' && (
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                placeholder="your_username"
                maxLength={20}
                pattern="^[a-zA-Z0-9_-]{3,20}$"
                title="3–20 characters: letters, numbers, underscores, hyphens"
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="you@example.com"
            />
          </div>

          {mode !== 'forgot' && (
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                minLength={8}
                maxLength={128}
                placeholder="••••••••"
              />
            </div>
          )}

          {mode === 'login' && loginFailed && (
            <button
              type="button"
              className="auth-link"
              onClick={() => switchMode('forgot')}
            >
              Forgot password?
            </button>
          )}

          {error && <p className="auth-error">{error}</p>}
          {success && <p className="auth-success">{success}</p>}

          <button type="submit" className="auth-submit" disabled={submitting}>
            {submitting
              ? 'Please wait...'
              : mode === 'login'
              ? 'Log In'
              : mode === 'signup'
              ? 'Create Account'
              : 'Send Reset Email'}
          </button>

          {mode === 'forgot' && (
            <button
              type="button"
              className="auth-link"
              onClick={() => switchMode('login')}
            >
              Back to Log In
            </button>
          )}
        </form>
      </div>
    </div>
  )
}

export default LoginPage
