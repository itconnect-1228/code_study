import { type ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth-store'

interface ProtectedRouteProps {
  children: ReactNode
  redirectTo?: string
}

/**
 * ProtectedRoute component - guards routes that require authentication
 *
 * Redirects to login page if user is not authenticated.
 * Preserves the attempted URL for redirect after login.
 *
 * Usage:
 * ```tsx
 * <Route
 *   path="/dashboard"
 *   element={
 *     <ProtectedRoute>
 *       <Dashboard />
 *     </ProtectedRoute>
 *   }
 * />
 * ```
 */
export default function ProtectedRoute({ children, redirectTo = '/login' }: ProtectedRouteProps) {
  const location = useLocation()
  const isAuthenticated = useAuthStore(state => state.isAuthenticated)
  const isLoading = useAuthStore(state => state.isLoading)

  // Show nothing while loading auth state
  if (isLoading) {
    return null
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />
  }

  // Render children if authenticated
  return <>{children}</>
}
