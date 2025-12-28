import { create } from "zustand";
import { devtools } from "zustand/middleware";

/**
 * User type - represents the authenticated user's information
 *
 * Note: JWT tokens are stored in HTTPOnly cookies for security.
 * This store only manages UI-relevant user information.
 */
export interface User {
  id: string;
  email: string;
  createdAt: string;
}

/**
 * Authentication state shape
 */
interface AuthState {
  /** Currently logged in user, or null if not authenticated */
  user: User | null;
  /** Whether the user is currently authenticated */
  isAuthenticated: boolean;
  /** Whether an auth operation (login/logout/refresh) is in progress */
  isLoading: boolean;
}

/**
 * Authentication actions
 */
interface AuthActions {
  /** Set the current user and update isAuthenticated accordingly */
  setUser: (user: User | null) => void;
  /** Set the loading state */
  setLoading: (loading: boolean) => void;
  /** Clear all auth state (used on logout) */
  clearAuth: () => void;
}

/**
 * Combined store type
 */
export type AuthStore = AuthState & AuthActions;

/**
 * Initial authentication state
 */
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
};

/**
 * Authentication store - manages user authentication state for the UI
 *
 * Important Design Decisions:
 * - JWT tokens are stored in HTTPOnly cookies (not in this store)
 * - This store only manages UI state (user info, loading states)
 * - isAuthenticated is derived from user being non-null
 *
 * Usage:
 * ```typescript
 * // In components
 * const { user, isAuthenticated } = useAuthStore()
 *
 * // For optimized subscriptions
 * const user = useUser()
 * const isAuth = useIsAuthenticated()
 * ```
 */
export const useAuthStore = create<AuthStore>()(
  devtools(
    (set) => ({
      ...initialState,

      setUser: (user) =>
        set(
          {
            user,
            isAuthenticated: user !== null,
          },
          false,
          "auth/setUser",
        ),

      setLoading: (loading) =>
        set(
          {
            isLoading: loading,
          },
          false,
          "auth/setLoading",
        ),

      clearAuth: () =>
        set(
          {
            ...initialState,
          },
          false,
          "auth/clearAuth",
        ),
    }),
    {
      name: "auth-store",
      enabled: import.meta.env.DEV,
    },
  ),
);

// Selector hooks for optimized component subscriptions
// These prevent unnecessary re-renders by subscribing only to specific parts of state

/**
 * Get current user - only re-renders when user changes
 */
export const useUser = () => useAuthStore((state) => state.user);

/**
 * Get authentication status - only re-renders when auth status changes
 */
export const useIsAuthenticated = () =>
  useAuthStore((state) => state.isAuthenticated);

/**
 * Get loading status - only re-renders when loading status changes
 */
export const useAuthLoading = () => useAuthStore((state) => state.isLoading);

export default useAuthStore;
