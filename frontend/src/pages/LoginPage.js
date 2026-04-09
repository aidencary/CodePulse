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

    const { error } =
      mode === 'login'
        ? await signIn(email, password)
        : await signUp(email, password, username)

    if (error) {
      setSubmitting(false)
      setError(error.message)
      return
    }

    if (mode === 'login') {
      const { data: aalData } =
        await supabase.auth.mfa.getAuthenticatorAssuranceLevel()

      if (
        aalData?.nextLevel === 'aal2' &&
        aalData?.currentLevel !== 'aal2'
      ) {
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
      setSuccess(
        'Account created! Check your email to confirm before logging in.'
      )
    }
  }

  const switchMode = (newMode) => {
    setMode(newMode)
    setError(null)
    setSuccess(null)
  }

  const handleMfaBack = async () => {
    await supabase.auth.signOut()
    setStep('credentials')
    setMfaFactorId(null)
    setMfaCode('')
    setError(null)
  }

  // Background gradient (darker toward bottom)
  const containerStyle = {
    minHeight: '100vh',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    background: 'linear-gradient(to bottom, #6A00E6 0%, #3B0070 50%, #12001F 100%)',
    backgroundAttachment: 'fixed',
  }

  const cardStyle = {
    border: '4px solid #9C6CFF',
    borderRadius: '12px',
    padding: '2rem',
    backgroundColor: '#1E0B3B',
    boxShadow: '0 0 20px rgba(0,0,0,0.5)',
    width: '360px',
    maxWidth: '90%',
  }

  if (step === 'mfa') {
    return (
      <div style={containerStyle}>
        <div style={cardStyle}>
          <h1 className="auth-title">CodePulse</h1>

          <p className="auth-mfa-hint">
            Enter the 6-digit code from your authenticator app.
          </p>

          <form onSubmit={handleSubmit} className="auth-form">
            <input
              type="text"
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value)}
              maxLength={6}
              placeholder="000000"
            />

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
    <div style={containerStyle}>
      <div style={cardStyle}>
        <h1 className="auth-title">Welcome To CodePulse</h1>

        {mode !== 'forgot' && (
          <div className="auth-toggle">
            <button onClick={() => switchMode('login')}>Log In</button>
            <button onClick={() => switchMode('signup')}>Sign Up</button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          {mode === 'signup' && (
            <input
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          )}

          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          {mode !== 'forgot' && (
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          )}

          {error && <p className="auth-error">{error}</p>}
          {success && <p className="auth-success">{success}</p>}

          <button type="submit" className="auth-submit" disabled={submitting}>
            {mode === 'login'
              ? 'Log In'
              : mode === 'signup'
              ? 'Create Account'
              : 'Send Reset Email'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default LoginPage