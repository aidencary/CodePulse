import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import InviteModal from '../InviteModal'

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockSession = { access_token: 'test-token' }

jest.mock('../../context/AuthContext', () => ({ useAuth: jest.fn() }))
const { useAuth } = require('../../context/AuthContext')

const mockInviteUser = jest.fn()
jest.mock('../../services/accountService', () => ({
  inviteUser: (...args) => mockInviteUser(...args),
}))

const mockToast = jest.fn()
jest.mock('../Toast', () => ({ useToast: () => mockToast }))

// ── Setup ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  jest.clearAllMocks()
  useAuth.mockReturnValue({ session: mockSession })
})

const renderModal = (onClose = jest.fn()) =>
  render(<InviteModal onClose={onClose} />)

// ── Tests ─────────────────────────────────────────────────────────────────────

// TC-ACCT-017
it('renders title, hint, email input, and action buttons', () => {
  renderModal()
  expect(screen.getByText(/invite a user/i)).toBeInTheDocument()
  expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /send invite/i })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
})

// TC-ACCT-018
it('disables Send Invite when email is empty', () => {
  renderModal()
  expect(screen.getByRole('button', { name: /send invite/i })).toBeDisabled()
})

// TC-ACCT-019
it('enables Send Invite once an email is entered', () => {
  renderModal()
  fireEvent.change(screen.getByLabelText(/email address/i), {
    target: { value: 'user@example.com' },
  })
  expect(screen.getByRole('button', { name: /send invite/i })).not.toBeDisabled()
})

// TC-ACCT-020
it('calls inviteUser with the token and trimmed email on submit', async () => {
  mockInviteUser.mockResolvedValue({})
  const onClose = jest.fn()
  renderModal(onClose)

  fireEvent.change(screen.getByLabelText(/email address/i), {
    target: { value: '  user@example.com  ' },
  })
  fireEvent.submit(
    screen.getByRole('button', { name: /send invite/i }).closest('form')
  )

  await waitFor(() => {
    expect(mockInviteUser).toHaveBeenCalledWith('test-token', 'user@example.com')
  })
})

// TC-ACCT-021
it('shows success toast and closes modal on successful invite', async () => {
  mockInviteUser.mockResolvedValue({})
  const onClose = jest.fn()
  renderModal(onClose)

  fireEvent.change(screen.getByLabelText(/email address/i), {
    target: { value: 'user@example.com' },
  })
  fireEvent.submit(
    screen.getByRole('button', { name: /send invite/i }).closest('form')
  )

  await waitFor(() => {
    expect(mockToast).toHaveBeenCalledWith(
      'Invite sent to user@example.com',
      'success'
    )
    expect(onClose).toHaveBeenCalled()
  })
})

// TC-ACCT-022
it('displays the error message and does not close on a failed invite', async () => {
  mockInviteUser.mockRejectedValue(new Error('User already registered'))
  const onClose = jest.fn()
  renderModal(onClose)

  fireEvent.change(screen.getByLabelText(/email address/i), {
    target: { value: 'existing@example.com' },
  })
  fireEvent.submit(
    screen.getByRole('button', { name: /send invite/i }).closest('form')
  )

  expect(await screen.findByText('User already registered')).toBeInTheDocument()
  expect(onClose).not.toHaveBeenCalled()
})

// TC-ACCT-023
it('calls onClose when Cancel is clicked', () => {
  const onClose = jest.fn()
  renderModal(onClose)
  fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
  expect(onClose).toHaveBeenCalled()
})

// TC-ACCT-024
it('calls onClose when the backdrop is clicked', () => {
  const onClose = jest.fn()
  const { container } = renderModal(onClose)
  fireEvent.click(container.firstChild) // backdrop div
  expect(onClose).toHaveBeenCalled()
})

// TC-ACCT-025
it('shows "Sending…" and disables the button while the request is in-flight', async () => {
  let resolve
  mockInviteUser.mockReturnValue(new Promise((res) => { resolve = res }))
  renderModal()

  fireEvent.change(screen.getByLabelText(/email address/i), {
    target: { value: 'user@example.com' },
  })
  fireEvent.submit(
    screen.getByRole('button', { name: /send invite/i }).closest('form')
  )

  const btn = await screen.findByRole('button', { name: /sending/i })
  expect(btn).toBeDisabled()
  resolve({})
})
