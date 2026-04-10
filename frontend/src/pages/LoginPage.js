import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import supabase from '../services/supabaseClient'
import '../styles/auth.css'

export function getPasswordStrength(pw) {
  if (!pw || pw.length < 6) return 0
  let criteria = 0
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) criteria++
  if (/\d/.test(pw)) criteria++
  if (/[^a-zA-Z0-9]/.test(pw)) criteria++
  if (pw.length >= 8 && criteria >= 3) return 3
  if (pw.length >= 8 && criteria >= 2) return 2
  return 1
}

const STRENGTH_CONFIG = [
  null,
  { label: 'Weak', color: '#f87171' },
  { label: 'Fair', color: '#fbbf24' },
  { label: 'Strong', color: '#86efac' },
]

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
  const [showPassword, setShowPassword] = useState(false)
  const [loginFailed, setLoginFailed] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const { signIn, signUp } = useAuth()
  const navigate = useNavigate()
  const heroRef = useRef(null)
  const learnMoreRef = useRef(null)
  const learnGridRef = useRef(null)
  const emailRef = useRef(null)

  useEffect(() => {
    if (step !== 'mfa') emailRef.current?.focus()
  }, [mode, step])

  useEffect(() => {
    const grid = learnGridRef.current
    if (!grid) return
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add('visible')
        })
      },
      { threshold: 0.15 }
    )
    grid.querySelectorAll('.learn-card').forEach((card) => observer.observe(card))
    return () => observer.disconnect()
  }, [])

  const scrollToLearnMore = () =>
    learnMoreRef.current?.scrollIntoView({ behavior: 'smooth' })

  const scrollToHero = () =>
    heroRef.current?.scrollIntoView({ behavior: 'smooth' })

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

    if (mode === 'signup' && password !== confirmPassword) {
      setError('Passwords do not match')
      setSubmitting(false)
      return
    }

    const { error } =
      mode === 'login'
        ? await signIn(email, password, rememberMe)
        : await signUp(email, password, username)

    if (error) {
      setSubmitting(false)
      setError(error.message)
      if (mode === 'login') setLoginFailed(true)
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
    setLoginFailed(false)
    setRememberMe(false)
    setConfirmPassword('')
    setShowConfirmPassword(false)
  }

  const handleOAuth = (provider) => {
    supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: window.location.origin + '/dashboard' },
    })
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
      <div className="login-page">
        <section className="auth-hero">
          <div className="auth-hero-inner">
            <div className="auth-logo-row">
              <img src="/CodePulseSlow.gif" alt="CodePulse logo" className="auth-logo-gif" />
              <span className="auth-logo-wordmark">odePulse</span>
            </div>
            <div className="auth-card">
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
        </section>
      </div>
    )
  }

  return (
    <div className="login-page">
      {/* ── Hero ── */}
      <section className="auth-hero" ref={heroRef}>
        <div className="auth-hero-inner">

          <div className="auth-logo-row">
            <img src="/CodePulseSlow.gif" alt="CodePulse logo" className="auth-logo-gif" />
            <span className="auth-logo-wordmark">odePulse</span>
          </div>

          <p className="auth-subtitle">
            A Hybrid Static Analysis and Machine Learning Pipeline
            for Automated Python Bug Detection
          </p>

          <div className="auth-card">
            {mode !== 'forgot' && (
              <div className="oauth-group">
                <button type="button" className="oauth-btn oauth-btn--google" onClick={() => handleOAuth('google')}>
                  <svg width="18" height="18" viewBox="0 0 24 24">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18A11.96 11.96 0 0 0 1 12c0 1.94.46 3.77 1.18 5.07l3.66-2.98z" fill="#FBBC05"/>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                  </svg>
                  Continue with Google
                </button>
                <button type="button" className="oauth-btn oauth-btn--github" onClick={() => handleOAuth('github')}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
                  </svg>
                  Continue with GitHub
                </button>
              </div>
            )}

            {mode !== 'forgot' && (
              <div className="oauth-divider">
                <span className="oauth-divider-line" />
                <span className="oauth-divider-text">or</span>
                <span className="oauth-divider-line" />
              </div>
            )}

            {mode !== 'forgot' && (
              <div className="auth-toggle">
                <div className={`auth-toggle-slider${mode === 'signup' ? ' right' : ''}`} />
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
                  ref={emailRef}
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  placeholder="user@example.com"
                />
              </div>

              {mode !== 'forgot' && (
                <div className="form-group">
                  <label htmlFor="password">Password</label>
                  <div className="password-wrapper">
                    <input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                      minLength={8}
                      maxLength={128}
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowPassword((v) => !v)}
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? (
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                          <circle cx="12" cy="12" r="3" fill="currentColor" stroke="none"/>
                          <line x1="1" y1="1" x2="23" y2="23"/>
                        </svg>
                      ) : (
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                          <circle cx="12" cy="12" r="3" fill="currentColor" stroke="none"/>
                        </svg>
                      )}
                    </button>
                  </div>
                </div>
              )}

              {mode === 'signup' && password.length > 0 && (() => {
                const strength = getPasswordStrength(password)
                const config = STRENGTH_CONFIG[strength]
                return config ? (
                  <div className="pw-strength">
                    <div className="pw-strength-bar">
                      {[1, 2, 3].map((seg) => (
                        <div
                          key={seg}
                          className={`pw-strength-segment${seg <= strength ? ' active' : ''}`}
                          style={seg <= strength ? { background: config.color } : undefined}
                        />
                      ))}
                    </div>
                    <span className="pw-strength-label" style={{ color: config.color }}>
                      {config.label}
                    </span>
                  </div>
                ) : null
              })()}

              {mode === 'signup' && (
                <div className="form-group">
                  <label htmlFor="confirm-password">Confirm Password</label>
                  <div className="password-wrapper">
                    <input
                      id="confirm-password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      autoComplete="new-password"
                      minLength={8}
                      maxLength={128}
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      className="password-toggle"
                      onClick={() => setShowConfirmPassword((v) => !v)}
                      aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                    >
                      {showConfirmPassword ? (
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
                          <circle cx="12" cy="12" r="3" fill="currentColor" stroke="none"/>
                          <line x1="1" y1="1" x2="23" y2="23"/>
                        </svg>
                      ) : (
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                          <circle cx="12" cy="12" r="3" fill="currentColor" stroke="none"/>
                        </svg>
                      )}
                    </button>
                  </div>
                </div>
              )}

              {mode === 'login' && (
                <label className="remember-me">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  Remember me
                </label>
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

              {mode === 'signup' && (
                <p className="auth-legal">
                  By creating an account you agree to our{' '}
                  <a href="/terms" target="_blank" rel="noopener noreferrer">Terms of Service</a>{' '}
                  and{' '}
                  <a href="/privacy" target="_blank" rel="noopener noreferrer">Privacy Policy</a>.
                </p>
              )}

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

          <div className="auth-scroll-divider" />
          <button className="auth-scroll-cue" onClick={scrollToLearnMore}>
            Learn more
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>
        </div>
      </section>

      {/* ── Learn more ── */}
      <section className="learn-more-section" ref={learnMoreRef}>
        <h2 className="learn-section-title">How CodePulse Works</h2>
        <p className="learn-section-intro">
          Software defects remain a leading cause of increased development cost and delayed deployment,
          especially as AI-generated code introduces subtle logical errors that traditional IDEs cannot catch.
          CodePulse addresses this with a three-stage hybrid pipeline that combines static analysis,
          large language model reasoning, and supervised learning into a single automated tool.
        </p>
        <div className="learn-grid" ref={learnGridRef}>
          <div className="learn-card">
            <span className="learn-card-icon">🌳</span>
            <h3>AST-Based Static Analysis</h3>
            <p>
              The first stage parses Python source code into an abstract syntax tree (AST) and applies
              rule-based checks to enforce PEP 8 compliance and verify structural correctness, catching
              formatting violations, undefined references, and other surface-level defects before any
              model is invoked.
            </p>
          </div>
          <div className="learn-card">
            <span className="learn-card-icon">🧠</span>
            <h3>GPT-4o-mini Semantic Prediction</h3>
            <p>
              A fine-tuned GPT-4o-mini model performs semantic bug prediction on the parsed code,
              identifying latent defects and logical errors that static rules cannot detect, including
              the subtle issues common in AI-assisted code generation that existing IDEs routinely miss.
            </p>
          </div>
          <div className="learn-card">
            <span className="learn-card-icon">🛡️</span>
            <h3>CodeBERT Validation Layer</h3>
            <p>
              A fine-tuned CodeBERT model, trained on the Defectors dataset of real-world vulnerability
              patterns, acts as a validation layer, filtering unreliable GPT predictions and providing
              localized confirmation of predicted defects to reduce false positives.
            </p>
          </div>
          <div className="learn-card">
            <span className="learn-card-icon">📊</span>
            <h3>Severity-Weighted Quality Score</h3>
            <p>
              All three stages feed into a severity-weighted score from 0 to 100 reflecting overall code
              quality. Results are surfaced instantly in the dashboard alongside a detailed bug report,
              built on FastAPI, React, Supabase, and HuggingFace Transformers.
            </p>
          </div>
          <div className="learn-card">
            <span className="learn-card-icon">⚠️</span>
            <h3>Why It Matters</h3>
            <p>
              Traditional IDEs detect syntax errors but miss semantic and logical bugs until runtime.
              As AI-assisted code generation grows, so does the risk of subtle defects passing unnoticed
              through standard tooling. CodePulse fills this gap with pre-execution defect analysis.
            </p>
          </div>
          <div className="learn-card">
            <span className="learn-card-icon">🔧</span>
            <h3>Built With</h3>
            <p>
              The system is implemented using FastAPI for the analysis backend, React for the web
              interface, Supabase for authentication and storage, and HuggingFace Transformers for
              model deployment, all connected through a single submission pipeline.
            </p>
          </div>
        </div>
        <p className="learn-section-credit">
          Research by Aiden Cary, Keller Willhite &amp; Zach Atchley, Faculty Mentor: Dr. Md Jobair Hossain Faruk
        </p>
        <p className="learn-legal-links">
          <a href="/terms" target="_blank" rel="noopener noreferrer">Terms of Service</a>
          {' · '}
          <a href="/privacy" target="_blank" rel="noopener noreferrer">Privacy Policy</a>
        </p>
        <button className="learn-show-less" onClick={scrollToHero}>
          Show less ↑
        </button>
        <p className="learn-copyright">
          &copy; {new Date().getFullYear()} CodePulseApp. All rights reserved.
        </p>
      </section>
    </div>
  )
}

export default LoginPage