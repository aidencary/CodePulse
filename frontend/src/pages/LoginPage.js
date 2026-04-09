import { useState, useRef } from 'react'
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
  const [showPassword, setShowPassword] = useState(false)

  const { signIn, signUp } = useAuth()
  const navigate = useNavigate()
  const heroRef = useRef(null)
  const learnMoreRef = useRef(null)

  const scrollToLearnMore = () =>
    learnMoreRef.current?.scrollIntoView({ behavior: 'smooth' })

  const scrollToHero = () =>
    heroRef.current?.scrollIntoView({ behavior: 'smooth' })

  // FR-AUTH-001
  // FR-AUTH-002
  // FR-AUTH-004
  // FR-AUTH-006
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setSubmitting(true)

    // FR-AUTH-004
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

    // FR-AUTH-006
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

    // FR-AUTH-002 (login) / FR-AUTH-001 (signup)
    const { error } = mode === 'login'
      ? await signIn(email, password)
      : await signUp(email, password, username)

    if (error) {
      setSubmitting(false)
      setError(error.message)
      if (mode === 'login') setLoginFailed(true)
      return
    }

    // FR-AUTH-004
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

          <button className="auth-scroll-cue" onClick={scrollToLearnMore}>
            Learn more ↓
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
        <div className="learn-grid">
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
