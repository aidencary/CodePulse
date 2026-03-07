import { useAuth } from '../context/AuthContext'

function DashboardPage() {
  const { user, signOut } = useAuth()

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Dashboard</h1>
      <p style={{ margin: '0.5rem 0 1.5rem' }}>Logged in as: <strong>{user?.email}</strong></p>
      <button onClick={signOut}>Sign Out</button>
    </div>
  )
}

export default DashboardPage
