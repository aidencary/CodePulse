import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import LoginPage from '../LoginPage'
import { useAuth } from '../../context/AuthContext'

jest.mock('../../context/AuthContext', () => ({
  useAuth: jest.fn(),
}))

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
}))

const mockResetPasswordForEmail = jest.fn()
jest.mock('../../services/supabaseClient', () => ({
  __esModule: true,
  default: {
    auth: {
      resetPasswordForEmail: (...args) => mockResetPasswordForEmail(...args),
    },
  },
}))

const mockSignIn = jest.fn()
const mockSignUp = jest.fn()

beforeEach(() => {
  jest.clearAllMocks()
  useAuth.mockReturnValue({ signIn: mockSignIn, signUp: mockSignUp })
})

const renderLoginPage = () =>
  render(<MemoryRouter><LoginPage /></MemoryRouter>)

// Helper: submit the form
const submitForm = () =>
  fireEvent.submit(screen.getByRole('form', { name: /authentication/i }))

describe('LoginPage', () => {
  it('renders Log In form by default without username field', () => {
    renderLoginPage()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.queryByLabelText(/username/i)).not.toBeInTheDocument()
  })

  it('shows username field after switching to Sign Up mode', () => {
    renderLoginPage()
    // Click the Sign Up toggle tab (not the submit button)
    fireEvent.click(screen.getByRole('button', { name: /sign up/i }))
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
  })

  it('calls signIn with email and password on login form submit', async () => {
    mockSignIn.mockResolvedValue({ error: null })
    renderLoginPage()
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } })
    submitForm()
    await waitFor(() =>
      expect(mockSignIn).toHaveBeenCalledWith('user@example.com', 'password123')
    )
  })

  it('calls signUp with email, password, and username on signup form submit', async () => {
    mockSignUp.mockResolvedValue({ error: null })
    renderLoginPage()
    fireEvent.click(screen.getByRole('button', { name: /sign up/i }))
    fireEvent.change(screen.getByLabelText(/username/i), { target: { value: 'testuser' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } })
    submitForm()
    await waitFor(() =>
      expect(mockSignUp).toHaveBeenCalledWith('user@example.com', 'password123', 'testuser')
    )
  })

  it('displays error message when signIn returns an error', async () => {
    mockSignIn.mockResolvedValue({ error: { message: 'Invalid login credentials' } })
    renderLoginPage()
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrongpassword' } })
    submitForm()
    expect(await screen.findByText('Invalid login credentials')).toBeInTheDocument()
  })
})

describe('LoginPage — forgot password', () => {
  /** Trigger a failed login so the "Forgot password?" link appears */
  async function triggerFailedLogin() {
    mockSignIn.mockResolvedValue({ error: { message: 'Invalid login credentials' } })
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } })
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrongpassword' } })
    submitForm()
    await screen.findByText('Invalid login credentials')
  }

  it('does not show "Forgot password?" before a failed login attempt', () => {
    renderLoginPage()
    expect(screen.queryByRole('button', { name: /forgot password/i })).not.toBeInTheDocument()
  })

  it('shows "Forgot password?" after a failed login attempt', async () => {
    renderLoginPage()
    await triggerFailedLogin()
    expect(screen.getByRole('button', { name: /forgot password/i })).toBeInTheDocument()
  })

  it('shows forgot password email form when "Forgot password?" is clicked', async () => {
    renderLoginPage()
    await triggerFailedLogin()
    fireEvent.click(screen.getByRole('button', { name: /forgot password/i }))
    expect(screen.getByRole('button', { name: /send reset email/i })).toBeInTheDocument()
    expect(screen.queryByLabelText(/^password$/i)).not.toBeInTheDocument()
  })

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

  it('shows error message when resetPasswordForEmail fails', async () => {
    mockResetPasswordForEmail.mockResolvedValue({ error: { message: 'User not found' } })
    renderLoginPage()
    await triggerFailedLogin()
    fireEvent.click(screen.getByRole('button', { name: /forgot password/i }))
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'nobody@example.com' } })
    fireEvent.submit(screen.getByRole('form', { name: /authentication/i }))
    expect(await screen.findByText('User not found')).toBeInTheDocument()
  })

  it('returns to login mode when "Back to Log In" is clicked', async () => {
    renderLoginPage()
    await triggerFailedLogin()
    fireEvent.click(screen.getByRole('button', { name: /forgot password/i }))
    fireEvent.click(screen.getByRole('button', { name: /back to log in/i }))
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /send reset email/i })).not.toBeInTheDocument()
  })
})
