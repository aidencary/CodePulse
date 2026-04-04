import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

// FR-AUTH-007
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  // NFR-USAB-001
  if (loading) return <div className="loading">Loading...</div>
  // FR-AUTH-007
  if (!user) return <Navigate to="/login" replace />
  return children
}

export default ProtectedRoute
