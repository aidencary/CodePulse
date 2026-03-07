import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import '../styles/auth.css'

function LoginPage() {
  const [mode, setMode] = useState('login') // 'login' | 'signup'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const { signIn, signUp } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    const { error } = mode === 'login'
      ? await signIn(email, password)
      : await signUp(email, password, username)

    setSubmitting(false)

    if (error) {
      setError(error.message)
    } else if (mode === 'login') {
      navigate('/dashboard')
    } else {
      setError('Account created! Check your email to confirm before logging in.')
    }
  }

  const switchMode = (newMode) => {
    setMode(newMode)
    setError(null)
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1 className="auth-title">CodePulse</h1>

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

        <form onSubmit={handleSubmit} className="auth-form">
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

          {error && <p className="auth-error">{error}</p>}

          <button type="submit" className="auth-submit" disabled={submitting}>
            {submitting
              ? 'Please wait...'
              : mode === 'login' ? 'Log In' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default LoginPage
