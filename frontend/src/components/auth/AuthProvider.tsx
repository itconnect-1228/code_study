import { useEffect, useState, type ReactNode } from 'react'
import { useAuthStore } from '@/stores/auth-store'
import { authService } from '@/services/auth-service'

interface AuthProviderProps {
  children: ReactNode
}

/**
 * AuthProvider - Initializes authentication state on app startup
 *
 * On mount, attempts to restore authentication state using the access token cookie.
 * If successful, sets the user in the auth store.
 * If failed (no valid token), clears auth state.
 */
export default function AuthProvider({ children }: AuthProviderProps) {
  const [isInitialized, setIsInitialized] = useState(false)
  const setUser = useAuthStore(state => state.setUser)
  const setLoading = useAuthStore(state => state.setLoading)
  const clearAuth = useAuthStore(state => state.clearAuth)

  useEffect(() => {
    const initializeAuth = async () => {
      setLoading(true)
      try {
        // Try to get current user using the access token cookie
        const user = await authService.getMe()
        setUser({
          id: user.id,
          email: user.email,
          createdAt: new Date().toISOString(),
        })
      } catch {
        // No valid access token, user is not authenticated
        clearAuth()
      } finally {
        setLoading(false)
        setIsInitialized(true)
      }
    }

    initializeAuth()
  }, [setUser, setLoading, clearAuth])

  // Show nothing until auth state is initialized
  if (!isInitialized) {
    return null
  }

  return <>{children}</>
}
