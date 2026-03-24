import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import SubmissionSidebar from '../SubmissionSidebar'
import { useAuth } from '../../context/AuthContext'
import {
  getSubmissions,
  renameSubmission,
  deleteSubmission,
  pinSubmission,
} from '../../services/submissionService'
import { useToast } from '../Toast'

jest.mock('../../context/AuthContext', () => ({
  useAuth: jest.fn(),
}))

jest.mock('../../services/submissionService', () => ({
  getSubmissions: jest.fn(),
  renameSubmission: jest.fn(),
  deleteSubmission: jest.fn(),
  pinSubmission: jest.fn(),
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

/** Helper: open the kebab menu for the first submission */
async function openKebab(index = 0) {
  const kebabs = screen.getAllByLabelText('Submission options')
  fireEvent.click(kebabs[index])
}

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

  it('shows rename input via kebab menu', async () => {
    renderSidebar()
    await screen.findByText('Calculator')
    openKebab(0)
    fireEvent.click(screen.getByText('Rename'))
    expect(screen.getByDisplayValue('Calculator')).toBeInTheDocument()
  })

  it('saves rename on Enter key', async () => {
    renameSubmission.mockResolvedValue()
    renderSidebar()
    await screen.findByText('Calculator')
    openKebab(0)
    fireEvent.click(screen.getByText('Rename'))
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
    await screen.findByText('Calculator')
    openKebab(0)
    fireEvent.click(screen.getByText('Rename'))
    const input = screen.getByDisplayValue('Calculator')
    fireEvent.keyDown(input, { key: 'Escape' })
    await waitFor(() => {
      expect(screen.queryByDisplayValue('Calculator')).not.toBeInTheDocument()
    })
    expect(renameSubmission).not.toHaveBeenCalled()
  })

  it('shows centered delete modal via kebab menu', async () => {
    renderSidebar()
    await screen.findByText('Calculator')
    openKebab(0)
    fireEvent.click(screen.getByText('Delete'))
    expect(screen.getByText('Delete Submission?')).toBeInTheDocument()
    expect(screen.getByText(/This will delete/)).toBeInTheDocument()
  })

  it('calls deleteSubmission when delete is confirmed', async () => {
    deleteSubmission.mockResolvedValue()
    renderSidebar()
    await screen.findByText('Calculator')
    openKebab(0)
    fireEvent.click(screen.getByText('Delete'))
    // Click the confirm button in the modal
    const confirmBtn = screen.getAllByRole('button', { name: 'Delete' })
    fireEvent.click(confirmBtn[confirmBtn.length - 1])
    await waitFor(() => {
      expect(deleteSubmission).toHaveBeenCalledWith('sub-1', 'fake-token')
    })
  })

  it('renders collapsed mini-bar when open is false', async () => {
    renderSidebar({ open: false })
    const sidebar = screen.getByRole('complementary')
    expect(sidebar).toHaveClass('sidebar-collapsed')
  })

  it('calls pinSubmission via kebab Star option', async () => {
    pinSubmission.mockResolvedValue({ pinned: true })
    renderSidebar()
    await screen.findByText('Calculator')
    openKebab(0)
    fireEvent.click(screen.getByText('Star'))
    await waitFor(() => {
      expect(pinSubmission).toHaveBeenCalledWith('sub-1', 'fake-token')
    })
  })

  it('shows pin star icon on pinned submissions', async () => {
    const pinnedSubmissions = [
      { ...mockSubmissions[0], pinned_at: '2025-06-01T00:00:00Z' },
      mockSubmissions[1],
    ]
    getSubmissions.mockResolvedValue(pinnedSubmissions)
    renderSidebar()
    await screen.findByText('Calculator')
    expect(screen.getByLabelText('Pinned')).toBeInTheDocument()
  })
})