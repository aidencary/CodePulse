import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ProtectedRoute from '../ProtectedRoute'
import { useAuth } from '../../context/AuthContext'

jest.mock('../../context/AuthContext', () => ({
  useAuth: jest.fn(),
}))

const renderWithRouter = (ui) => render(<MemoryRouter>{ui}</MemoryRouter>)

describe('ProtectedRoute', () => {
  // TC-AUTH-005
  it('renders loading indicator while auth state is initializing', () => {
    useAuth.mockReturnValue({ user: null, loading: true })
    renderWithRouter(<ProtectedRoute><div>Dashboard</div></ProtectedRoute>)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument()
  })

  // TC-AUTH-006
  it('redirects to /login when user is not authenticated', () => {
    useAuth.mockReturnValue({ user: null, loading: false })
    renderWithRouter(<ProtectedRoute><div>Dashboard</div></ProtectedRoute>)
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument()
  })

  // TC-AUTH-007
  it('renders children when user is authenticated', () => {
    useAuth.mockReturnValue({ user: { id: 'abc', email: 'test@example.com' }, loading: false })
    renderWithRouter(<ProtectedRoute><div>Dashboard</div></ProtectedRoute>)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })
})
