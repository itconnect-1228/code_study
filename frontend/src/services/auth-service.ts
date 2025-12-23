import { apiClient } from './api-client'

interface UserResponse {
  id: string
  email: string
  skill_level: string
}

interface LoginResponse {
  access_token: string
  token_type: string
  user: UserResponse
}

export interface User {
  id: string
  email: string
  skillLevel: string
}

/**
 * Transforms backend user format to frontend User type
 */
const transformUser = (userData: UserResponse): User => ({
  id: userData.id,
  email: userData.email,
  skillLevel: userData.skill_level,
})

/**
 * Authentication service - handles all auth-related API calls
 *
 * Note: JWT tokens are managed via HTTPOnly cookies by the backend.
 * This service only handles user data transformation.
 */
export const authService = {
  /**
   * Register a new user
   * @param email - User's email address
   * @param password - User's password
   * @returns User data
   */
  async register(email: string, password: string): Promise<User> {
    const response = await apiClient.post<UserResponse>('/auth/register', {
      email,
      password,
    })

    return transformUser(response.data)
  },

  /**
   * Login with email and password
   * @param email - User's email address
   * @param password - User's password
   * @returns User data
   */
  async login(email: string, password: string): Promise<User> {
    const response = await apiClient.post<LoginResponse>('/auth/login', {
      email,
      password,
    })

    return transformUser(response.data.user)
  },

  /**
   * Logout the current user
   * Invalidates the refresh token cookie
   */
  async logout(): Promise<void> {
    await apiClient.post('/auth/logout')
  },

  /**
   * Refresh the access token using the refresh token cookie
   * @returns Updated user data
   */
  async refresh(): Promise<User> {
    const response = await apiClient.post<LoginResponse>('/auth/refresh')

    return transformUser(response.data.user)
  },
}

export default authService
