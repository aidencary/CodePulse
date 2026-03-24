import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import SubmissionSidebar from '../SubmissionSidebar'
import { useAuth } from '../../context/AuthContext'
import {
  getSubmissions,
  renameSubmission,
  deleteSubmission,
} from '../../services/submissionService'
import { useToast } from '../Toast'

jest.mock('../../context/AuthContext', () => ({
  useAuth: jest.fn(),
}))

jest.mock('../../services/submissionService', () => ({
  getSubmissions: jest.fn(),
  renameSubmission: jest.fn(),
  deleteSubmission: jest.fn(),
}))

jest.mock('../Toast', () => ({
  useToast: jest.fn(),
}))

const mockUser = { id: 'user-123' }
const mockSession = { access_token: 'fake-token' }

const mockSubmissions = [
  {
    submission_id: 'sub-1',
    name: 'Calculator',
    code: 'print(1)',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    submission_id: 'sub-2',
    name: null,
    code: 'def foo(): pass',
    created_at: '2024-01-02T00:00:00Z',
  },
]

const mockOnSelect = jest.fn()
const mockToast = jest.fn()

beforeEach(() => {
  jest.clearAllMocks()
  useAuth.mockReturnValue({ user: mockUser, session: mockSession })
  useToast.mockReturnValue(mockToast)
  getSubmissions.mockResolvedValue(mockSubmissions)
})

const renderSidebar = (props = {}) =>
  render(
    <SubmissionSidebar
      onSelect={mockOnSelect}
      activeId={null}
      onClose={jest.fn()}
      onOpen={jest.fn()}
      open={true}
      {...props}
    />
  )

describe('SubmissionSidebar', () => {
  it('renders submissions with names', async () => {
    renderSidebar()
    expect(await screen.findByText('Calculator')).toBeInTheDocument()
  })

  it('falls back to first code line when name is null', async () => {
    renderSidebar()
    expect(await screen.findByText('def foo(): pass')).toBeInTheDocument()
  })

  it('filters submissions by search input', async () => {
    renderSidebar()
    await screen.findByText('Calculator')
    const searchInput = screen.getByPlaceholderText(/search/i)
    fireEvent.change(searchInput, { target: { value: 'calc' } })
    expect(screen.getByText('Calculator')).toBeInTheDocument()
    expect(screen.queryByText('def foo(): pass')).not.toBeInTheDocument()
  })

  it('shows rename input on double-click', async () => {
    renderSidebar()
    const title = await screen.findByText('Calculator')
    fireEvent.doubleClick(title)
    expect(screen.getByDisplayValue('Calculator')).toBeInTheDocument()
  })

  it('saves rename on Enter key', async () => {
    renameSubmission.mockResolvedValue()
    renderSidebar()
    const title = await screen.findByText('Calculator')
    fireEvent.doubleClick(title)
    const input = screen.getByDisplayValue('Calculator')
    fireEvent.change(input, { target: { value: 'My Calc' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    await waitFor(() => {
      expect(renameSubmission).toHaveBeenCalledWith(
        'sub-1',
        'My Calc',
        'fake-token'
      )
    })
  })

  it('cancels rename on Escape key without calling API', async () => {
    renderSidebar()
    const title = await screen.findByText('Calculator')
    fireEvent.doubleClick(title)
    const input = screen.getByDisplayValue('Calculator')
    fireEvent.keyDown(input, { key: 'Escape' })
    await waitFor(() => {
      expect(screen.queryByDisplayValue('Calculator')).not.toBeInTheDocument()
    })
    expect(renameSubmission).not.toHaveBeenCalled()
  })

  it('shows delete confirmation when trash button is clicked', async () => {
    renderSidebar()
    await screen.findByText('Calculator')
    const deleteButtons = screen.getAllByLabelText('Delete submission')
    fireEvent.click(deleteButtons[0])
    expect(screen.getByText('Delete this submission?')).toBeInTheDocument()
  })

  it('calls deleteSubmission when delete is confirmed', async () => {
    deleteSubmission.mockResolvedValue()
    renderSidebar()
    await screen.findByText('Calculator')
    const deleteButtons = screen.getAllByLabelText('Delete submission')
    fireEvent.click(deleteButtons[0])
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))
    await waitFor(() => {
      expect(deleteSubmission).toHaveBeenCalledWith('sub-1', 'fake-token')
    })
  })

  it('renders collapsed mini-bar when open is false', async () => {
    renderSidebar({ open: false })
    const sidebar = screen.getByRole('complementary')
    expect(sidebar).toHaveClass('sidebar-collapsed')
  })
})
