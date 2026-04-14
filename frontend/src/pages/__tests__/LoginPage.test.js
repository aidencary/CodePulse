import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import LoginPage, { getPasswordStrength } from '../LoginPage'
import { useAuth } from '../../context/AuthContext'

// jsdom does not provide IntersectionObserver
beforeAll(() => {
  global.IntersectionObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
})

jest.mock('../../context/AuthContext', () => ({
  useAuth: jest.fn(),
}))

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
}))

const mockResetPasswordForEmail = jest.fn()
const mockGetAAL = jest.fn()
const mockListFactors = jest.fn()
const mockChallenge = jest.fn()
const mockVerify = jest.fn()
const mockSignOut = jest.fn()
const mockSignInWithOAuth = jest.fn()

jest.mock('../../services/supabaseClient', () => ({
  __esModule: true,
  default: {
    auth: {
      resetPasswordForEmail: (...args) => mockResetPasswordForEmail(...args),
      signOut: (...args) => mockSignOut(...args),
      signInWithOAuth: (...args) => mockSignInWithOAuth(...args),
      mfa: {
        getAuthenticatorAssuranceLevel: (...args) => mockGetAAL(...args),
        listFactors: (...args) => mockListFactors(...args),
        challenge: (...args) => mockChallenge(...args),
        verify: (...args) => mockVerify(...args),
      },
    },
  },
}))

const mockSignIn = jest.fn()
const mockSignUp = jest.fn()

beforeEach(() => {
  jest.clearAllMocks()
  useAuth.mockReturnValue({ signIn: mockSignIn, signUp: mockSignUp })
  // Default: no MFA enrolled — aal1 only, no step-up required
  mockGetAAL.mockResolvedValue({ data: { currentLevel: 'aal1', nextLevel: 'aal1' } })
  mockListFactors.mockResolvedValue({ data: { totp: [] } })
  mockSignOut.mockResolvedValue({})
})

const renderLoginPage = () =>
  render(<MemoryRouter><LoginPage /></MemoryRouter>)

// Helper: submit the form
// NOTE: uses exact label 'Password' (not /password/i) to avoid matching the
// "Show password" aria-label on the visibility toggle button.
const getPasswordInput = () => screen.getByLabelText('Password')

const submitForm = () =>
  fireEvent.submit(screen.getByRole('form', { name: /authentication/i }))

describe('LoginPage', () => {
  // TC-AUTH-023
  it('renders Log In form by default without username field', () => {
    renderLoginPage()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(getPasswordInput()).toBeInTheDocument()
    expect(screen.queryByLabelText(/username/i)).not.toBeInTheDocument()
  })

  // TC-AUTH-024
  it('shows username field after switching to Sign Up mode', () => {
    renderLoginPage()
    // Click the Sign Up toggle tab (not the submit button)
    fireEvent.click(screen.getByRole('button', { name: /sign up/i }))
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
  })

  // TC-AUTH-025
  it('calls signIn with email and password on login form submit', async () => {
    mockSignIn.mockResolvedValue({ error: null })
    renderLoginPage()
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.change(getPasswordInput(), { target: { value: 'password123' } })
    submitForm()
    await waitFor(() =>
      expect(mockSignIn).toHaveBeenCalledWith('user@example.com', 'password123', false)
    )
  })

  // TC-AUTH-026
  it('calls signUp with email, password, and username on signup form submit', async () => {
    mockSignUp.mockResolvedValue({ error: null })
    renderLoginPage()
    fireEvent.click(screen.getByRole('button', { name: /sign up/i }))
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.change(getPasswordInput(), { target: { value: 'password123' } })
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'password123' } })
    submitForm()
    await waitFor(() =>
      expect(mockSignUp).toHaveBeenCalledWith('user@example.com', 'password123', 'testuser')
    )
  })

  // TC-AUTH-027
  it('displays error message when signIn returns an error', async () => {
    mockSignIn.mockResolvedValue({ error: { message: 'Invalid login credentials' } })
    renderLoginPage()
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.change(getPasswordInput(), { target: { value: 'wrongpassword' } })
    submitForm()
    expect(await screen.findByText('Invalid login credentials')).toBeInTheDocument()
  })

  // TC-AUTH-040
  it('password field starts as type="password" (masked)', () => {
    renderLoginPage()
    expect(getPasswordInput()).toHaveAttribute('type', 'password')
  })

  // TC-AUTH-041
  it('toggles password field to type="text" when show-password button is clicked', () => {
    renderLoginPage()
    const toggle = screen.getByRole('button', { name: /show password/i })
    fireEvent.click(toggle)
    expect(getPasswordInput()).toHaveAttribute('type', 'text')
  })

  // TC-AUTH-042
  it('toggles password field back to type="password" on second click', () => {
    renderLoginPage()
    const toggle = screen.getByRole('button', { name: /show password/i })
    fireEvent.click(toggle)
    fireEvent.click(screen.getByRole('button', { name: /hide password/i }))
    expect(getPasswordInput()).toHaveAttribute('type', 'password')
  })

  // TC-AUTH-046
  it('renders "Remember me" checkbox in login mode', () => {
    renderLoginPage()
    expect(screen.getByLabelText(/remember me/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/remember me/i)).not.toBeChecked()
  })

  // TC-AUTH-047
  it('hides "Remember me" checkbox in signup mode', () => {
    renderLoginPage()
    fireEvent.click(screen.getByRole('button', { name: /sign up/i }))
    expect(screen.queryByLabelText(/remember me/i)).not.toBeInTheDocument()
  })

  // TC-AUTH-048
  it('hides "Remember me" checkbox in forgot password mode', async () => {
    mockSignIn.mockResolvedValue({ error: { message: 'Invalid login credentials' } })
    renderLoginPage()
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.change(getPasswordInput(), { target: { value: 'wrong' } })
    submitForm()
    await screen.findByText('Invalid login credentials')
    fireEvent.click(screen.getByRole('button', { name: /forgot password/i }))
    expect(screen.queryByLabelText(/remember me/i)).not.toBeInTheDocument()
  })

  // TC-AUTH-049
  it('renders "Confirm Password" field in signup mode', () => {
    renderLoginPage()
    fireEvent.click(screen.getByRole('button', { name: /sign up/i }))
    expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument()
  })

  // TC-AUTH-050
  it('hides "Confirm Password" field in login mode', () => {
    renderLoginPage()
    expect(screen.queryByLabelText('Confirm Password')).not.toBeInTheDocument()
  })

  // TC-AUTH-051
  it('shows error and blocks signUp when passwords do not match', async () => {
    renderLoginPage()
    fireEvent.click(screen.getByRole('button', { name: /sign up/i }))
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.change(getPasswordInput(), { target: { value: 'password123' } })
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'different456' } })
    submitForm()
    expect(await screen.findByText('Passwords do not match')).toBeInTheDocument()
    expect(mockSignUp).not.toHaveBeenCalled()
  })

  // TC-AUTH-052
  it('calls signUp when passwords match', async () => {
    mockSignUp.mockResolvedValue({ error: null })
    renderLoginPage()
    fireEvent.click(screen.getByRole('button', { name: /sign up/i }))
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.change(getPasswordInput(), { target: { value: 'password123' } })
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'password123' } })
    submitForm()
    await waitFor(() =>
      expect(mockSignUp).toHaveBeenCalledWith('user@example.com', 'password123', 'testuser')
    )
  })

  // TC-AUTH-053
  it('has independent show/hide toggles for password and confirm password', () => {
    renderLoginPage()
    fireEvent.click(screen.getByRole('button', { name: /sign up/i }))
    const showPw = screen.getByRole('button', { name: /^show password$/i })
    const showConfirm = screen.getByRole('button', { name: /show confirm password/i })
    fireEvent.click(showPw)
    expect(getPasswordInput()).toHaveAttribute('type', 'text')
    expect(screen.getByLabelText('Confirm Password')).toHaveAttribute('type', 'password')
    fireEvent.click(showConfirm)
    expect(screen.getByLabelText('Confirm Password')).toHaveAttribute('type', 'text')
  })

  // TC-AUTH-060
  it('shows legal notice in signup mode', () => {
    renderLoginPage()
    fireEvent.click(screen.getByRole('button', { name: /sign up/i }))
    expect(screen.getByText(/by creating an account/i)).toBeInTheDocument()
  })

  // TC-AUTH-061
  it('hides legal notice in login mode', () => {
    renderLoginPage()
    expect(screen.queryByText(/by creating an account/i)).not.toBeInTheDocument()
  })

  // TC-AUTH-062
  it('hides legal notice in forgot password mode', async () => {
    mockSignIn.mockResolvedValue({ error: { message: 'fail' } })
    renderLoginPage()
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@b.com' } })
    fireEvent.change(getPasswordInput(), { target: { value: 'wrong' } })
    submitForm()
    await screen.findByText('fail')
    fireEvent.click(screen.getByRole('button', { name: /forgot password/i }))
    expect(screen.queryByText(/by creating an account/i)).not.toBeInTheDocument()
  })

  // TC-AUTH-043
  it('renders the "Learn more" scroll button', () => {
    renderLoginPage()
    expect(screen.getByRole('button', { name: /learn more/i })).toBeInTheDocument()
  })

  // TC-AUTH-044
  it('renders the learn-more section with all pipeline stage headings', () => {
    renderLoginPage()
    expect(screen.getByText(/AST-Based Static Analysis/i)).toBeInTheDocument()
    expect(screen.getByText(/GPT-4o-mini Semantic Prediction/i)).toBeInTheDocument()
    expect(screen.getByText(/CodeBERT Validation Layer/i)).toBeInTheDocument()
    expect(screen.getByText(/Severity-Weighted Quality Score/i)).toBeInTheDocument()
    expect(screen.getByText(/Why It Matters/i)).toBeInTheDocument()
    expect(screen.getByText(/Built With/i)).toBeInTheDocument()
  })

  // TC-AUTH-045
  it('renders the "Show less" button in the learn-more section', () => {
    renderLoginPage()
    expect(screen.getByRole('button', { name: /show less/i })).toBeInTheDocument()
  })
})

describe('LoginPage — forgot password', () => {
  /** Trigger a failed login so the "Forgot password?" link appears */
  async function triggerFailedLogin() {
    mockSignIn.mockResolvedValue({ error: { message: 'Invalid login credentials' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.change(getPasswordInput(), { target: { value: 'wrongpassword' } })
    submitForm()
    await screen.findByText('Invalid login credentials')
  }

  // TC-AUTH-028
  it('does not show "Forgot password?" before a failed login attempt', () => {
    renderLoginPage()
    expect(screen.queryByRole('button', { name: /forgot password/i })).not.toBeInTheDocument()
  })

  // TC-AUTH-029
  it('shows "Forgot password?" after a failed login attempt', async () => {
    renderLoginPage()
    await triggerFailedLogin()
    expect(screen.getByRole('button', { name: /forgot password/i })).toBeInTheDocument()
  })

  // TC-AUTH-030
  it('shows forgot password email form when "Forgot password?" is clicked', async () => {
    renderLoginPage()
    await triggerFailedLogin()
    fireEvent.click(screen.getByRole('button', { name: /forgot password/i }))
    expect(screen.getByRole('button', { name: /send reset email/i })).toBeInTheDocument()
    expect(screen.queryByLabelText('Password')).not.toBeInTheDocument()
  })

  // TC-AUTH-031
  it('calls resetPasswordForEmail with the entered email', async () => {
    mockResetPasswordForEmail.mockResolvedValue({ error: null })
    renderLoginPage()
    await triggerFailedLogin()
    fireEvent.click(screen.getByRole('button', { name: /forgot password/i }))
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.submit(screen.getByRole('form', { name: /authentication/i }))
    await waitFor(() =>
      expect(mockResetPasswordForEmail).toHaveBeenCalledWith(
        'user@example.com',
        expect.objectContaining({ redirectTo: expect.stringContaining('/reset-password') })
      )
    )
  })

  // TC-AUTH-032
  it('shows success message after reset email is sent', async () => {
    mockResetPasswordForEmail.mockResolvedValue({ error: null })
    renderLoginPage()
    await triggerFailedLogin()
    fireEvent.click(screen.getByRole('button', { name: /forgot password/i }))
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.submit(screen.getByRole('form', { name: /authentication/i }))
    expect(
      await screen.findByText(/check your email for a password reset link/i)
    ).toBeInTheDocument()
  })

  // TC-AUTH-033
  it('shows error message when resetPasswordForEmail fails', async () => {
    mockResetPasswordForEmail.mockResolvedValue({ error: { message: 'User not found' } })
    renderLoginPage()
    await triggerFailedLogin()
    fireEvent.click(screen.getByRole('button', { name: /forgot password/i }))
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'nobody@example.com' } })
    fireEvent.submit(screen.getByRole('form', { name: /authentication/i }))
    expect(await screen.findByText('User not found')).toBeInTheDocument()
  })

  // TC-AUTH-034
  it('returns to login mode when "Back to Log In" is clicked', async () => {
    renderLoginPage()
    await triggerFailedLogin()
    fireEvent.click(screen.getByRole('button', { name: /forgot password/i }))
    fireEvent.click(screen.getByRole('button', { name: /back to log in/i }))
    expect(getPasswordInput()).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /send reset email/i })).not.toBeInTheDocument()
  })
})

describe('LoginPage — MFA step-up', () => {
  const mfaFactor = { id: 'factor-1', status: 'verified', factor_type: 'totp' }

  /** Sign in successfully, then set mocks so MFA step-up is triggered */
  async function signInWithMfa() {
    mockSignIn.mockResolvedValue({ error: null })
    mockGetAAL.mockResolvedValue({ data: { currentLevel: 'aal1', nextLevel: 'aal2' } })
    mockListFactors.mockResolvedValue({ data: { totp: [mfaFactor] } })
    renderLoginPage()
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.change(getPasswordInput(), { target: { value: 'password123' } })
    submitForm()
    // Wait for MFA form
    await screen.findByRole('form', { name: /two-factor authentication/i })
  }

  // TC-AUTH-035
  it('shows MFA code input after successful login when AAL step-up is required', async () => {
    await signInWithMfa()
    expect(screen.getByLabelText(/authentication code/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^verify$/i })).toBeInTheDocument()
  })

  // TC-AUTH-036
  it('does not show MFA step when nextLevel is aal1', async () => {
    mockSignIn.mockResolvedValue({ error: null })
    // Default mocks already set nextLevel: 'aal1' — no MFA step-up
    renderLoginPage()
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.change(getPasswordInput(), { target: { value: 'password123' } })
    submitForm()
    // MFA form should never appear
    await waitFor(() => expect(mockGetAAL).toHaveBeenCalled())
    expect(screen.queryByRole('form', { name: /two-factor authentication/i })).not.toBeInTheDocument()
  })

  // TC-AUTH-037
  it('calls challenge and verify with factorId and code on MFA submit', async () => {
    mockChallenge.mockResolvedValue({ data: { id: 'challenge-1' }, error: null })
    mockVerify.mockResolvedValue({ error: null })
    await signInWithMfa()
    fireEvent.change(screen.getByLabelText(/authentication code/i), { target: { value: '123456' } })
    fireEvent.submit(screen.getByRole('form', { name: /two-factor authentication/i }))
    await waitFor(() => expect(mockChallenge).toHaveBeenCalledWith({ factorId: 'factor-1' }))
    await waitFor(() =>
      expect(mockVerify).toHaveBeenCalledWith({
        factorId: 'factor-1',
        challengeId: 'challenge-1',
        code: '123456',
      })
    )
  })

  // TC-AUTH-038
  it('shows "Invalid code" error on verify failure', async () => {
    mockChallenge.mockResolvedValue({ data: { id: 'challenge-1' }, error: null })
    mockVerify.mockResolvedValue({ error: { message: 'Invalid TOTP token' } })
    await signInWithMfa()
    fireEvent.change(screen.getByLabelText(/authentication code/i), { target: { value: '000000' } })
    fireEvent.submit(screen.getByRole('form', { name: /two-factor authentication/i }))
    expect(await screen.findByText(/invalid code/i)).toBeInTheDocument()
  })

  // TC-AUTH-039
  it('signs out and returns to credentials when "Back to Log In" is clicked', async () => {
    await signInWithMfa()
    fireEvent.click(screen.getByRole('button', { name: /back to log in/i }))
    await waitFor(() => expect(mockSignOut).toHaveBeenCalled())
    expect(screen.getByRole('form', { name: /authentication/i })).toBeInTheDocument()
  })
})

describe('getPasswordStrength', () => {
  // TC-AUTH-054
  it('returns 0 for empty or short passwords', () => {
    expect(getPasswordStrength('')).toBe(0)
    expect(getPasswordStrength('abc')).toBe(0)
    expect(getPasswordStrength('Ab1!x')).toBe(0)
  })

  // TC-AUTH-055
  it('returns 1 (Weak) for >= 6 chars with few criteria', () => {
    expect(getPasswordStrength('abcdef')).toBe(1)
    expect(getPasswordStrength('abcdefgh')).toBe(1)
  })

  // TC-AUTH-056
  it('returns 2 (Fair) for >= 8 chars with 2 criteria', () => {
    expect(getPasswordStrength('Abcdefg1')).toBe(2)
    expect(getPasswordStrength('abcdef!1')).toBe(2)
  })

  // TC-AUTH-057
  it('returns 3 (Strong) for >= 8 chars with all 3 criteria', () => {
    expect(getPasswordStrength('Abcdef1!')).toBe(3)
    expect(getPasswordStrength('MyP@ss99')).toBe(3)
  })
})

describe('LoginPage — password strength bar', () => {
  // TC-AUTH-058
  it('does not render strength bar in login mode', () => {
    renderLoginPage()
    fireEvent.change(getPasswordInput(), { target: { value: 'password123' } })
    expect(screen.queryByText('Weak')).not.toBeInTheDocument()
    expect(screen.queryByText('Fair')).not.toBeInTheDocument()
    expect(screen.queryByText('Strong')).not.toBeInTheDocument()
  })

  // TC-AUTH-059
  it('renders strength bar in signup mode when typing', () => {
    renderLoginPage()
    fireEvent.click(screen.getByRole('button', { name: /sign up/i }))
    fireEvent.change(getPasswordInput(), { target: { value: 'Abcdef1!' } })
    expect(screen.getByText('Strong')).toBeInTheDocument()
  })
})

describe('LoginPage — OAuth buttons', () => {
  // TC-AUTH-063
  it('renders Google and GitHub buttons in login mode', () => {
    renderLoginPage()
    expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /continue with github/i })).toBeInTheDocument()
  })

  // TC-AUTH-064
  it('renders Google and GitHub buttons in signup mode', () => {
    renderLoginPage()
    fireEvent.click(screen.getByRole('button', { name: /sign up/i }))
    expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /continue with github/i })).toBeInTheDocument()
  })

  // TC-AUTH-065
  it('hides OAuth buttons in forgot password mode', async () => {
    mockSignIn.mockResolvedValue({ error: { message: 'fail' } })
    renderLoginPage()
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'a@b.com' } })
    fireEvent.change(getPasswordInput(), { target: { value: 'wrong' } })
    submitForm()
    await screen.findByText('fail')
    fireEvent.click(screen.getByRole('button', { name: /forgot password/i }))
    expect(screen.queryByRole('button', { name: /continue with google/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /continue with github/i })).not.toBeInTheDocument()
  })

  // TC-AUTH-066
  it('calls signInWithOAuth with "google" when Google button is clicked', () => {
    renderLoginPage()
    fireEvent.click(screen.getByRole('button', { name: /continue with google/i }))
    expect(mockSignInWithOAuth).toHaveBeenCalledWith({
      provider: 'google',
      options: { redirectTo: expect.stringContaining('/dashboard') },
    })
  })

  // TC-AUTH-067
  it('calls signInWithOAuth with "github" when GitHub button is clicked', () => {
    renderLoginPage()
    fireEvent.click(screen.getByRole('button', { name: /continue with github/i }))
    expect(mockSignInWithOAuth).toHaveBeenCalledWith({
      provider: 'github',
      options: { redirectTo: expect.stringContaining('/dashboard') },
    })
  })
})
