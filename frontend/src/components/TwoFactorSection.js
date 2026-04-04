import { useEffect, useState } from 'react'
import supabase from '../services/supabaseClient'
import { useToast } from './Toast'

function TwoFactorSection() {
  const toast = useToast()
  const [loading, setLoading] = useState(true)
  const [factorId, setFactorId] = useState(null)
  const [enrollData, setEnrollData] = useState(null) // { factorId, qrCode, secret }
  const [verifyCode, setVerifyCode] = useState('')
  const [enrollErr, setEnrollErr] = useState(null)
  const [mfaErr, setMfaErr] = useState(null)
  const [enrolling, setEnrolling] = useState(false)
  const [verifying, setVerifying] = useState(false)
  const [disabling, setDisabling] = useState(false)

  useEffect(() => {
    supabase.auth.mfa.listFactors().then(({ data }) => {
      const verified = data?.totp?.find((f) => f.status === 'verified')
      setFactorId(verified?.id ?? null)
      setLoading(false)
    })
  }, [])

  // FR-AUTH-003
  const handleEnroll = async () => {
    setEnrolling(true)
    setEnrollErr(null)

    // Clean up any leftover unverified factors before enrolling
    const { data: existing } = await supabase.auth.mfa.listFactors()
    const unverified = existing?.totp?.filter((f) => f.status !== 'verified') ?? []
    for (const f of unverified) {
      await supabase.auth.mfa.unenroll({ factorId: f.id })
    }

    const { data, error } = await supabase.auth.mfa.enroll({ factorType: 'totp' })
    setEnrolling(false)
    if (error) {
      setEnrollErr(error.message)
      return
    }
    setEnrollData({
      factorId: data.id,
      qrCode: data.totp.qr_code,
      secret: data.totp.secret,
    })
  }

  // FR-AUTH-004
  const handleVerify = async (e) => {
    e.preventDefault()
    setVerifying(true)
    setEnrollErr(null)
    const { error } = await supabase.auth.mfa.challengeAndVerify({
      factorId: enrollData.factorId,
      code: verifyCode.trim(),
    })
    setVerifying(false)
    if (error) {
      setEnrollErr(error.message)
      return
    }
    setFactorId(enrollData.factorId)
    setEnrollData(null)
    setVerifyCode('')
    toast('Two-factor authentication enabled', 'success')
  }

  // FR-AUTH-005
  const handleDisable = async () => {
    setDisabling(true)
    setMfaErr(null)
    const { error } = await supabase.auth.mfa.unenroll({ factorId })
    setDisabling(false)
    if (error) {
      setMfaErr(error.message)
      return
    }
    setFactorId(null)
    toast('Two-factor authentication disabled', 'success')
  }

  if (loading) return null

  return (
    <section className="account-section">
      <h2 className="account-section-title">Security</h2>

      {/* ── Enrolled state ── */}
      {factorId && (
        <>
          <p className="mfa-enabled-badge">2FA Enabled ✓</p>
          <p className="account-hint">
            Your account is protected with a TOTP authenticator app.
          </p>
          {mfaErr && <div className="account-error">{mfaErr}</div>}
          <button
            className="account-btn account-btn--danger"
            onClick={handleDisable}
            disabled={disabling}
            type="button"
          >
            {disabling ? 'Disabling...' : 'Disable 2FA'}
          </button>
        </>
      )}

      {/* ── Enrollment in progress ── */}
      {enrollData && (
        <>
          <p className="account-hint">
            Scan this QR code with Microsoft Authenticator or any TOTP app.
          </p>
          <img
            src={enrollData.qrCode}
            alt="2FA QR code"
            className="mfa-qr"
          />
          <p className="account-hint">
            Can&apos;t scan? Enter this key manually:
          </p>
          <p className="mfa-secret">{enrollData.secret}</p>
          <form onSubmit={handleVerify} aria-label="verify 2fa">
            <div className="account-field">
              <label className="account-label" htmlFor="mfa-verify-code">
                6-Digit Code
              </label>
              <input
                id="mfa-verify-code"
                className="account-input"
                type="text"
                inputMode="numeric"
                value={verifyCode}
                onChange={(e) => setVerifyCode(e.target.value)}
                maxLength={6}
                placeholder="000000"
                autoComplete="one-time-code"
              />
            </div>
            {enrollErr && <div className="account-error">{enrollErr}</div>}
            <button
              type="submit"
              className="account-btn account-btn--primary"
              disabled={verifying || verifyCode.trim().length !== 6}
            >
              {verifying ? 'Verifying...' : 'Verify'}
            </button>
          </form>
        </>
      )}

      {/* ── Not enrolled ── */}
      {!factorId && !enrollData && (
        <>
          <p className="account-hint">
            Add an extra layer of security by requiring a code from your
            authenticator app at login.
          </p>
          {enrollErr && <div className="account-error">{enrollErr}</div>}
          <button
            className="account-btn account-btn--primary"
            onClick={handleEnroll}
            disabled={enrolling}
            type="button"
          >
            {enrolling ? 'Setting up...' : 'Enable 2FA'}
          </button>
        </>
      )}
    </section>
  )
}

export default TwoFactorSection
