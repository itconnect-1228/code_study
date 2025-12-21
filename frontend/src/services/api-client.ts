import axios, { type AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'

/**
 * API Base URL - defaults to localhost:8000/api/v1 for development
 * Override with VITE_API_BASE_URL environment variable for production
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

/**
 * Default timeout for API requests (30 seconds)
 * Note: Long-running operations like AI document generation may need
 * individual timeout overrides
 */
const DEFAULT_TIMEOUT = 30000

/**
 * Axios instance configured for the backend API
 *
 * Features:
 * - Base URL automatically prefixed to all requests
 * - Credentials (cookies) included for JWT authentication
 * - JSON content type headers set by default
 * - Request/response interceptors for extensibility
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: DEFAULT_TIMEOUT,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

/**
 * Request interceptor - runs before each request is sent
 *
 * Current functionality:
 * - Passes through the request config unchanged
 *
 * Future extensions:
 * - Add CSRF token to headers
 * - Log requests in development mode
 * - Add request timestamps for performance tracking
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Future: Add CSRF token, logging, etc.
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

/**
 * Response interceptor - runs after each response is received
 *
 * Current functionality:
 * - Passes through successful responses unchanged
 * - Rejects errors for handling by the calling code
 *
 * Future extensions:
 * - Handle 401 errors with automatic redirect to login
 * - Implement automatic token refresh on 401
 * - Log response times in development mode
 * - Retry failed requests with exponential backoff
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: AxiosError) => {
    // Future: Handle 401 redirect, token refresh, etc.
    return Promise.reject(error)
  }
)

export default apiClient
