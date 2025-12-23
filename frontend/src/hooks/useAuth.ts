import { useCallback } from 'react'
import { authService, type User as ServiceUser } from '@/services/auth-service'
import { useAuthStore, type User as StoreUser } from '@/stores/auth-store'

/**
 * Transform service user to store user format
 */
const transformToStoreUser = (serviceUser: ServiceUser): StoreUser => ({
  id: serviceUser.id,
  email: serviceUser.email,
  createdAt: new Date().toISOString(),
})

/**
 * Custom hook for authentication operations
 *
 * Combines authService API calls with authStore state management.
 * Provides a unified interface for login, logout, and refresh operations.
 *
 * Usage:
 * ```tsx
 * function MyComponent() {
 *   const { user, isAuthenticated, isLoading, login, logout, refresh } = useAuth()
 *
 *   const handleLogin = async () => {
 *     try {
 *       await login('email@example.com', 'password')
 *       // User is now logged in
 *     } catch (error) {
 *       // Handle error
 *     }
 *   }
 * }
 * ```
 */
export function useAuth() {
  const user = useAuthStore(state => state.user)
  const isAuthenticated = useAuthStore(state => state.isAuthenticated)
  const isLoading = useAuthStore(state => state.isLoading)
  const setUser = useAuthStore(state => state.setUser)
  const setLoading = useAuthStore(state => state.setLoading)
  const clearAuth = useAuthStore(state => state.clearAuth)

  /**
   * Login with email and password
   */
  const login = useCallback(
    async (email: string, password: string) => {
      setLoading(true)
      try {
        const serviceUser = await authService.login(email, password)
        setUser(transformToStoreUser(serviceUser))
      } catch (error) {
        clearAuth()
        throw error
      } finally {
        setLoading(false)
      }
    },
    [setLoading, setUser, clearAuth]
  )

  /**
   * Logout the current user
   */
  const logout = useCallback(async () => {
    setLoading(true)
    try {
      await authService.logout()
    } finally {
      clearAuth()
      setLoading(false)
    }
  }, [setLoading, clearAuth])

  /**
   * Refresh the current session
   */
  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const serviceUser = await authService.refresh()
      setUser(transformToStoreUser(serviceUser))
    } catch (error) {
      clearAuth()
      throw error
    } finally {
      setLoading(false)
    }
  }, [setLoading, setUser, clearAuth])

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refresh,
  }
}

export default useAuth
