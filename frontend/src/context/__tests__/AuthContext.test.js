import { render, act } from '@testing-library/react'
import { AuthProvider, useAuth } from '../AuthContext'
import supabase from '../../services/supabaseClient'

jest.mock('../../services/supabaseClient', () => ({
  auth: {
    onAuthStateChange: jest.fn(),
    signInWithPassword: jest.fn(),
    signUp: jest.fn(),
    signOut: jest.fn(),
  },
}))

const mockUnsubscribe = jest.fn()

beforeEach(() => {
  jest.clearAllMocks()
  supabase.auth.onAuthStateChange.mockReturnValue({
    data: { subscription: { unsubscribe: mockUnsubscribe } },
  })
})

// Helper: renders a component that captures the auth context value
function AuthConsumer({ onValue }) {
  const auth = useAuth()
  onValue(auth)
  return null
}

function renderWithAuth(onValue) {
  return render(
    <AuthProvider>
      <AuthConsumer onValue={onValue} />
    </AuthProvider>
  )
}

describe('AuthContext', () => {
  it('subscribes to onAuthStateChange on mount and unsubscribes on unmount', () => {
    const { unmount } = renderWithAuth(() => {})
    expect(supabase.auth.onAuthStateChange).toHaveBeenCalledTimes(1)
    unmount()
    expect(mockUnsubscribe).toHaveBeenCalledTimes(1)
  })

  it('signIn calls supabase.auth.signInWithPassword with email and password', async () => {
    supabase.auth.signInWithPassword.mockResolvedValue({ error: null })
    let authValue
    renderWithAuth((v) => { authValue = v })
    await act(async () => {
      await authValue.signIn('user@example.com', 'password123')
    })
    expect(supabase.auth.signInWithPassword).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'password123',
    })
  })

  it('signUp calls supabase.auth.signUp with email, password, and username metadata', async () => {
    supabase.auth.signUp.mockResolvedValue({ error: null })
    let authValue
    renderWithAuth((v) => { authValue = v })
    await act(async () => {
      await authValue.signUp('user@example.com', 'password123', 'testuser')
    })
    expect(supabase.auth.signUp).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'password123',
      options: { data: { username: 'testuser' } },
    })
  })

  it('signOut calls supabase.auth.signOut', async () => {
    supabase.auth.signOut.mockResolvedValue({ error: null })
    let authValue
    renderWithAuth((v) => { authValue = v })
    await act(async () => {
      await authValue.signOut()
    })
    expect(supabase.auth.signOut).toHaveBeenCalledTimes(1)
  })
})
