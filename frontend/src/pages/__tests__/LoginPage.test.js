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

const mockSignIn = jest.fn()
const mockSignUp = jest.fn()

beforeEach(() => {
  jest.clearAllMocks()
  useAuth.mockReturnValue({ signIn: mockSignIn, signUp: mockSignUp })
})

const renderLoginPage = () =>
  render(<MemoryRouter><LoginPage /></MemoryRouter>)

// Helper: submit the form via the email input's parent form
const submitForm = () =>
  fireEvent.submit(screen.getByLabelText(/email/i).closest('form'))

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
    await waitFor(() =>
      expect(screen.getByText('Invalid login credentials')).toBeInTheDocument()
    )
  })
})
