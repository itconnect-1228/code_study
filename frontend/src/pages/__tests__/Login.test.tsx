import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import Login from '../Login'
import { authService } from '@/services/auth-service'

// Mock the auth service
vi.mock('@/services/auth-service', () => ({
  authService: {
    register: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
  },
}))

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the login form', () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    )

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /login|sign in/i })).toBeInTheDocument()
  })

  it('renders page title', () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    )

    expect(screen.getByText(/welcome back/i)).toBeInTheDocument()
  })

  it('renders link to register page', () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    )

    expect(
      screen.getByRole('link', { name: /register|sign up|create account/i })
    ).toBeInTheDocument()
  })

  it('calls login service and navigates to dashboard on success', async () => {
    const user = userEvent.setup()
    vi.mocked(authService.login).mockResolvedValue({
      id: '123',
      email: 'test@example.com',
      skillLevel: 'beginner',
    } as never)

    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    )

    await user.type(screen.getByLabelText(/email/i), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /login|sign in/i }))

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith('test@example.com', 'password123')
    })

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('displays error message on login failure', async () => {
    const user = userEvent.setup()
    vi.mocked(authService.login).mockRejectedValue({
      response: { data: { detail: 'Invalid credentials' } },
    })

    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    )

    await user.type(screen.getByLabelText(/email/i), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword')
    await user.click(screen.getByRole('button', { name: /login|sign in/i }))

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })
  })

  it('shows loading state while logging in', async () => {
    const user = userEvent.setup()
    vi.mocked(authService.login).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    )

    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    )

    await user.type(screen.getByLabelText(/email/i), 'test@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /login|sign in/i }))

    expect(screen.getByRole('button', { name: /logging in|signing in/i })).toBeDisabled()
  })
})
