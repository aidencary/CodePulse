import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import TwoFactorSection from '../TwoFactorSection'
import { useToast } from '../Toast'

const mockListFactors = jest.fn()
const mockEnroll = jest.fn()
const mockChallengeAndVerify = jest.fn()
const mockUnenroll = jest.fn()

jest.mock('../../services/supabaseClient', () => ({
  __esModule: true,
  default: {
    auth: {
      mfa: {
        listFactors: (...a) => mockListFactors(...a),
        enroll: (...a) => mockEnroll(...a),
        challengeAndVerify: (...a) => mockChallengeAndVerify(...a),
        unenroll: (...a) => mockUnenroll(...a),
      },
    },
  },
}))

jest.mock('../Toast', () => ({ useToast: jest.fn() }))

const mockToast = jest.fn()

const noFactors = { data: { totp: [] } }
const verifiedFactor = { data: { totp: [{ id: 'factor-1', status: 'verified', factor_type: 'totp' }] } }
const enrollResponse = {
  data: {
    id: 'factor-new',
    totp: { qr_code: 'data:image/png;base64,abc123', secret: 'JBSWY3DPEHPK3PXP' },
  },
  error: null,
}

beforeEach(() => {
  jest.clearAllMocks()
  useToast.mockReturnValue(mockToast)
  mockListFactors.mockResolvedValue(noFactors)
})

const renderSection = () => render(<TwoFactorSection />)

describe('TwoFactorSection', () => {
  // TC-AUTH-008
  it('shows "Enable 2FA" when no verified factor exists', async () => {
    renderSection()
    expect(await screen.findByRole('button', { name: /enable 2fa/i })).toBeInTheDocument()
  })

  // TC-AUTH-009
  it('shows "2FA Enabled" and "Disable 2FA" when a verified factor exists', async () => {
    mockListFactors.mockResolvedValue(verifiedFactor)
    renderSection()
    expect(await screen.findByText(/2fa enabled/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /disable 2fa/i })).toBeInTheDocument()
  })

  // TC-AUTH-010
  it('clicking "Enable 2FA" calls enroll and shows QR code', async () => {
    mockEnroll.mockResolvedValue(enrollResponse)
    renderSection()
    fireEvent.click(await screen.findByRole('button', { name: /enable 2fa/i }))
    await waitFor(() => expect(mockEnroll).toHaveBeenCalledWith({ factorType: 'totp' }))
    expect(await screen.findByAltText(/qr code/i)).toBeInTheDocument()
  })

  // TC-AUTH-011
  // TC-AUTH-011
  it('QR code img has src matching the returned qr_code URI', async () => {
    mockEnroll.mockResolvedValue(enrollResponse)
    renderSection()
    fireEvent.click(await screen.findByRole('button', { name: /enable 2fa/i }))
    const img = await screen.findByAltText(/qr code/i)
    expect(img).toHaveAttribute('src', 'data:image/png;base64,abc123')
  })

  // TC-AUTH-012
  // TC-AUTH-012
  it('displays the manual secret after enrollment', async () => {
    mockEnroll.mockResolvedValue(enrollResponse)
    renderSection()
    fireEvent.click(await screen.findByRole('button', { name: /enable 2fa/i }))
    expect(await screen.findByText('JBSWY3DPEHPK3PXP')).toBeInTheDocument()
  })

  // TC-AUTH-013
  // TC-AUTH-013
  it('calls challengeAndVerify with correct factorId and trimmed code on Verify', async () => {
    mockEnroll.mockResolvedValue(enrollResponse)
    mockChallengeAndVerify.mockResolvedValue({ error: null })
    renderSection()
    fireEvent.click(await screen.findByRole('button', { name: /enable 2fa/i }))
    await screen.findByAltText(/qr code/i)
    fireEvent.change(screen.getByLabelText(/6-digit code/i), { target: { value: '123456' } })
    fireEvent.submit(screen.getByRole('form', { name: /verify 2fa/i }))
    await waitFor(() =>
      expect(mockChallengeAndVerify).toHaveBeenCalledWith({
        factorId: 'factor-new',
        code: '123456',
      })
    )
  })

  // TC-AUTH-014
  // TC-AUTH-014
  it('shows error on failed verification', async () => {
    mockEnroll.mockResolvedValue(enrollResponse)
    mockChallengeAndVerify.mockResolvedValue({ error: { message: 'Invalid TOTP code' } })
    renderSection()
    fireEvent.click(await screen.findByRole('button', { name: /enable 2fa/i }))
    await screen.findByAltText(/qr code/i)
    fireEvent.change(screen.getByLabelText(/6-digit code/i), { target: { value: '000000' } })
    fireEvent.submit(screen.getByRole('form', { name: /verify 2fa/i }))
    expect(await screen.findByText('Invalid TOTP code')).toBeInTheDocument()
  })

  // TC-AUTH-015
  it('shows "2FA Enabled ✓" and removes QR code on successful verification', async () => {
    mockEnroll.mockResolvedValue(enrollResponse)
    mockChallengeAndVerify.mockResolvedValue({ error: null })
    renderSection()
    fireEvent.click(await screen.findByRole('button', { name: /enable 2fa/i }))
    await screen.findByAltText(/qr code/i)
    fireEvent.change(screen.getByLabelText(/6-digit code/i), { target: { value: '123456' } })
    fireEvent.submit(screen.getByRole('form', { name: /verify 2fa/i }))
    expect(await screen.findByText(/2fa enabled/i)).toBeInTheDocument()
    expect(screen.queryByAltText(/qr code/i)).not.toBeInTheDocument()
  })

  // TC-AUTH-016
  // TC-AUTH-016
  it('calls unenroll with the factorId when "Disable 2FA" is clicked', async () => {
    mockListFactors.mockResolvedValue(verifiedFactor)
    mockUnenroll.mockResolvedValue({ error: null })
    renderSection()
    fireEvent.click(await screen.findByRole('button', { name: /disable 2fa/i }))
    await waitFor(() => expect(mockUnenroll).toHaveBeenCalledWith({ factorId: 'factor-1' }))
  })

  // TC-AUTH-017
  it('shows "Enable 2FA" again after successful unenroll', async () => {
    mockListFactors.mockResolvedValue(verifiedFactor)
    mockUnenroll.mockResolvedValue({ error: null })
    renderSection()
    fireEvent.click(await screen.findByRole('button', { name: /disable 2fa/i }))
    expect(await screen.findByRole('button', { name: /enable 2fa/i })).toBeInTheDocument()
  })

  // TC-AUTH-018
  // TC-AUTH-018
  it('shows error on failed unenroll', async () => {
    mockListFactors.mockResolvedValue(verifiedFactor)
    mockUnenroll.mockResolvedValue({ error: { message: 'Failed to unenroll' } })
    renderSection()
    fireEvent.click(await screen.findByRole('button', { name: /disable 2fa/i }))
    expect(await screen.findByText('Failed to unenroll')).toBeInTheDocument()
  })
})
