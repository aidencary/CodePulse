import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ResetPasswordPage from '../ResetPasswordPage'
import { useToast } from '../../components/Toast'

const mockOnAuthStateChange = jest.fn()
const mockUpdateUser = jest.fn()
let capturedAuthCallback = null

jest.mock('../../services/supabaseClient', () => ({
  __esModule: true,
  default: {
    auth: {
      onAuthStateChange: (...args) => mockOnAuthStateChange(...args),
      updateUser: (...args) => mockUpdateUser(...args),
    },
  },
}))

jest.mock('../../components/Toast', () => ({
  useToast: jest.fn(),
}))

const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

const mockToast = jest.fn()

beforeEach(() => {
  jest.clearAllMocks()
  capturedAuthCallback = null
  mockOnAuthStateChange.mockImplementation((cb) => {
    capturedAuthCallback = cb
    return { data: { subscription: { unsubscribe: jest.fn() } } }
  })
  useToast.mockReturnValue(mockToast)
})

const renderPage = () =>
  render(<MemoryRouter><ResetPasswordPage /></MemoryRouter>)

/** Fire the PASSWORD_RECOVERY event to set ready=true */
function fireRecovery() {
  act(() => { capturedAuthCallback('PASSWORD_RECOVERY') })
}

describe('ResetPasswordPage', () => {
  // TC-AUTH-040
  it('shows loading state while waiting for PASSWORD_RECOVERY event', () => {
    renderPage()
    expect(screen.getByText(/processing reset link/i)).toBeInTheDocument()
    expect(screen.queryByRole('form')).not.toBeInTheDocument()
  })

  // TC-AUTH-041
  it('shows password form once PASSWORD_RECOVERY fires', () => {
    renderPage()
    fireRecovery()
    expect(screen.getByRole('form', { name: /reset password/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/new password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
  })

  // TC-AUTH-042
  it('shows error when passwords do not match', () => {
    renderPage()
    fireRecovery()
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'password123' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'different1' } })
    fireEvent.submit(screen.getByRole('form', { name: /reset password/i }))
    expect(screen.getByText('Passwords do not match.')).toBeInTheDocument()
    expect(mockUpdateUser).not.toHaveBeenCalled()
  })

  // TC-AUTH-043
  it('shows error when password is shorter than 8 characters', () => {
    renderPage()
    fireRecovery()
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'short' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'short' } })
    fireEvent.submit(screen.getByRole('form', { name: /reset password/i }))
    expect(screen.getByText('Password must be at least 8 characters.')).toBeInTheDocument()
    expect(mockUpdateUser).not.toHaveBeenCalled()
  })

  // TC-AUTH-044
  it('calls updateUser with the new password on valid submit', async () => {
    mockUpdateUser.mockResolvedValue({ error: null })
    renderPage()
    fireRecovery()
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'newpassword1' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'newpassword1' } })
    fireEvent.submit(screen.getByRole('form', { name: /reset password/i }))
    await waitFor(() =>
      expect(mockUpdateUser).toHaveBeenCalledWith({ password: 'newpassword1' })
    )
  })

  // TC-AUTH-045
  it('calls toast and navigates to /login on success', async () => {
    mockUpdateUser.mockResolvedValue({ error: null })
    renderPage()
    fireRecovery()
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'newpassword1' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'newpassword1' } })
    fireEvent.submit(screen.getByRole('form', { name: /reset password/i }))
    await waitFor(() =>
      expect(mockToast).toHaveBeenCalledWith('Password updated! Please log in.', 'success')
    )
    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })

  // TC-AUTH-046
  it('shows error message when updateUser returns an error (expired link)', async () => {
    mockUpdateUser.mockResolvedValue({ error: { message: 'Token has expired or is invalid' } })
    renderPage()
    fireRecovery()
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'newpassword1' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'newpassword1' } })
    fireEvent.submit(screen.getByRole('form', { name: /reset password/i }))
    expect(await screen.findByText('Token has expired or is invalid')).toBeInTheDocument()
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  // TC-AUTH-047
  it('disables submit button while submitting', async () => {
    mockUpdateUser.mockReturnValue(new Promise(() => {})) // never resolves
    renderPage()
    fireRecovery()
    fireEvent.change(screen.getByLabelText(/new password/i), { target: { value: 'newpassword1' } })
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'newpassword1' } })
    fireEvent.submit(screen.getByRole('form', { name: /reset password/i }))
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /please wait/i })).toBeDisabled()
    )
  })
})
