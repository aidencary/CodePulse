import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AccountPage from '../AccountPage'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../../components/Toast'
import {
  getProfile,
  updateProfile,
  changePassword,
} from '../../services/accountService'

jest.mock('../../context/AuthContext', () => ({
  useAuth: jest.fn(),
}))

jest.mock('../../components/Toast', () => ({
  useToast: jest.fn(),
}))

jest.mock('../../services/accountService', () => ({
  getProfile: jest.fn(),
  updateProfile: jest.fn(),
  changePassword: jest.fn(),
}))

const mockNavigate = jest.fn()

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

const mockProfile = {
  id: 'user-123',
  email: 'test@example.com',
  username: 'testuser',
  role: 'developer',
  profile_picture: null,
  created_at: '2024-01-15T12:00:00Z',
}

const mockToast = jest.fn()

beforeEach(() => {
  jest.clearAllMocks()
  useAuth.mockReturnValue({
    session: { access_token: 'fake-token' },
    signOut: jest.fn(),
    refreshSession: jest.fn().mockResolvedValue(),
  })
  useToast.mockReturnValue(mockToast)
  getProfile.mockResolvedValue(mockProfile)
})

const renderAccountPage = () =>
  render(
    <MemoryRouter>
      <AccountPage />
    </MemoryRouter>
  )

describe('AccountPage', () => {
  // TC-ACCT-026
  it('renders all sections after profile loads', async () => {
    renderAccountPage()
    await waitFor(() => {
      expect(screen.getByText('Profile')).toBeInTheDocument()
    })
    expect(screen.getByText('Profile Picture')).toBeInTheDocument()
    // "Change Password" appears as both h2 and button — use heading role
    expect(
      screen.getByRole('heading', { name: 'Change Password' })
    ).toBeInTheDocument()
    expect(screen.getByText('Report a Bug')).toBeInTheDocument()
    expect(screen.getByText('Danger Zone')).toBeInTheDocument()
  })

  // TC-ACCT-036
  it('renders the report bug mailto link with correct address', async () => {
    renderAccountPage()
    await waitFor(() => {
      expect(screen.getByText('Report a Bug')).toBeInTheDocument()
    })
    const link = screen.getByRole('link', { name: /codepulsepp@gmail\.com/i })
    expect(link).toHaveAttribute('href', expect.stringContaining('codepulsepp@gmail.com'))
  })

  // TC-ACCT-027
  it('displays profile data in form fields', async () => {
    renderAccountPage()
    await waitFor(() => {
      expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument()
    })
    expect(screen.getByDisplayValue('testuser')).toBeInTheDocument()
    expect(screen.getByDisplayValue('developer')).toBeInTheDocument()
  })

  // TC-ACCT-037
  it('displays formatted "Member since" date', async () => {
    renderAccountPage()
    await waitFor(() => {
      expect(screen.getByDisplayValue('January 15, 2024')).toBeInTheDocument()
    })
    expect(screen.getByDisplayValue('January 15, 2024')).toHaveAttribute('readOnly')
  })

  // TC-ACCT-028
  it('shows validation error when username is too short', async () => {
    renderAccountPage()
    await waitFor(() => {
      expect(screen.getByDisplayValue('testuser')).toBeInTheDocument()
    })
    const usernameInput = screen.getByDisplayValue('testuser')
    fireEvent.change(usernameInput, { target: { value: 'ab' } })
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))
    await waitFor(() => {
      expect(screen.getByText(/3–20 characters/)).toBeInTheDocument()
    })
  })

  // TC-ACCT-029
  it('shows validation error when username has invalid characters', async () => {
    renderAccountPage()
    await waitFor(() => {
      expect(screen.getByDisplayValue('testuser')).toBeInTheDocument()
    })
    const usernameInput = screen.getByDisplayValue('testuser')
    fireEvent.change(usernameInput, { target: { value: 'test user!' } })
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))
    await waitFor(() => {
      expect(
        screen.getByText(/letters, numbers, underscores, and hyphens/)
      ).toBeInTheDocument()
    })
  })

  // TC-ACCT-030
  it('calls updateProfile and shows success toast on valid update', async () => {
    const updatedProfile = { ...mockProfile, username: 'newname' }
    updateProfile.mockResolvedValue(updatedProfile)
    renderAccountPage()
    await waitFor(() => {
      expect(screen.getByDisplayValue('testuser')).toBeInTheDocument()
    })
    const usernameInput = screen.getByDisplayValue('testuser')
    fireEvent.change(usernameInput, { target: { value: 'newname' } })
    fireEvent.click(screen.getByRole('button', { name: /save changes/i }))
    await waitFor(() => {
      expect(updateProfile).toHaveBeenCalledWith('fake-token', {
        username: 'newname',
      })
    })
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith('Profile updated', 'success')
    })
  })

  // TC-ACCT-031
  it('shows error when new password and confirm password do not match', async () => {
    renderAccountPage()
    await waitFor(() => {
      expect(screen.getByLabelText('Current Password')).toBeInTheDocument()
    })
    fireEvent.change(screen.getByLabelText('Current Password'), {
      target: { value: 'oldpass123' },
    })
    fireEvent.change(screen.getByLabelText('New Password'), {
      target: { value: 'newpass123' },
    })
    fireEvent.change(screen.getByLabelText('Confirm New Password'), {
      target: { value: 'different123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /change password/i }))
    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument()
    })
  })

  // TC-ACCT-032
  it('shows error when new password is too short', async () => {
    renderAccountPage()
    await waitFor(() => {
      expect(screen.getByLabelText('Current Password')).toBeInTheDocument()
    })
    fireEvent.change(screen.getByLabelText('Current Password'), {
      target: { value: 'oldpass123' },
    })
    fireEvent.change(screen.getByLabelText('New Password'), {
      target: { value: 'short' },
    })
    fireEvent.change(screen.getByLabelText('Confirm New Password'), {
      target: { value: 'short' },
    })
    fireEvent.click(screen.getByRole('button', { name: /change password/i }))
    await waitFor(() => {
      expect(screen.getByText(/8–128 characters/)).toBeInTheDocument()
    })
  })

  // TC-ACCT-033
  it('calls changePassword and shows success toast on valid password change', async () => {
    changePassword.mockResolvedValue()
    renderAccountPage()
    await waitFor(() => {
      expect(screen.getByLabelText('Current Password')).toBeInTheDocument()
    })
    fireEvent.change(screen.getByLabelText('Current Password'), {
      target: { value: 'oldpass123' },
    })
    fireEvent.change(screen.getByLabelText('New Password'), {
      target: { value: 'newpass1234' },
    })
    fireEvent.change(screen.getByLabelText('Confirm New Password'), {
      target: { value: 'newpass1234' },
    })
    fireEvent.click(screen.getByRole('button', { name: /change password/i }))
    await waitFor(() => {
      expect(changePassword).toHaveBeenCalledWith('fake-token', {
        current_password: 'oldpass123',
        new_password: 'newpass1234',
      })
    })
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(
        'Password changed successfully',
        'success'
      )
    })
  })

  // TC-ACCT-034
  it('shows delete confirmation modal when Delete Account is clicked', async () => {
    renderAccountPage()
    await waitFor(() => {
      expect(screen.getByText('Danger Zone')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: /delete account/i }))
    expect(screen.getByText(/type/i)).toBeInTheDocument()
    expect(
      screen.getByPlaceholderText('Type your username')
    ).toBeInTheDocument()
  })

  // TC-ACCT-035
  it('keeps delete button disabled until username matches', async () => {
    renderAccountPage()
    await waitFor(() => {
      expect(screen.getByText('Danger Zone')).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: /delete account/i }))
    const confirmBtn = screen.getByRole('button', { name: /delete my account/i })
    expect(confirmBtn).toBeDisabled()
    fireEvent.change(screen.getByPlaceholderText('Type your username'), {
      target: { value: 'testuser' },
    })
    expect(confirmBtn).not.toBeDisabled()
  })
})
