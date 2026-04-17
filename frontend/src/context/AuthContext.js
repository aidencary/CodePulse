import { createContext, useContext, useEffect, useState } from 'react'
import supabase from '../services/supabaseClient'
import { getProfile } from '../services/accountService'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [cachedProfile, setCachedProfile] = useState(null)

  function prefetchProfile(token) {
    if (!token) return
    getProfile(token).then(setCachedProfile).catch(() => {})
  }

  useEffect(() => {
    // Hydrate immediately from local cache before waiting for the event
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
      prefetchProfile(session?.access_token)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        // Session-only login: if the tab was closed and reopened, sign out
        if (
          session &&
          localStorage.getItem('codepulse-remember-me') === 'false' &&
          !sessionStorage.getItem('codepulse-session-active')
        ) {
          setLoading(false)
          supabase.auth.signOut()
          localStorage.removeItem('codepulse-remember-me')
          return
        }

        setSession(session)
        setUser(session?.user ?? null)
        setLoading(false)
        if (session) {
          prefetchProfile(session.access_token)
        } else {
          setCachedProfile(null)
        }
      }
    )
    return () => subscription.unsubscribe()
  }, [])

  /**
   * Sign up a new user. Passes username in metadata so the DB trigger
   * can populate profiles.username automatically.
   */
  const signUp = (email, password, username) =>
    supabase.auth.signUp({
      email,
      password,
      options: { data: { username } },
    })

  const signIn = async (email, password, rememberMe = true) => {
    const result = await supabase.auth.signInWithPassword({ email, password })
    if (!result.error) {
      if (rememberMe) {
        localStorage.setItem('codepulse-remember-me', 'true')
      } else {
        localStorage.setItem('codepulse-remember-me', 'false')
        sessionStorage.setItem('codepulse-session-active', '1')
      }
    }
    return result
  }

  const signOut = () => {
    localStorage.removeItem('codepulse-remember-me')
    sessionStorage.removeItem('codepulse-session-active')
    return supabase.auth.signOut()
  }

  const refreshSession = async () => {
    const { data } = await supabase.auth.refreshSession()
    if (data?.session) {
      setSession(data.session)
      setUser(data.session.user)
    }
  }

  return (
    <AuthContext.Provider value={{ user, session, loading, cachedProfile, setCachedProfile, signUp, signIn, signOut, refreshSession }}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Hook to access auth state and actions from any component.
 * session.access_token is the JWT to pass to the backend API.
 */
export function useAuth() {
  return useContext(AuthContext)
}
