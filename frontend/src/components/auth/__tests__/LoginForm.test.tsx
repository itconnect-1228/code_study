import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import LoginForm from '../LoginForm'

describe('LoginForm', () => {
  it('renders email and password fields', () => {
    render(<LoginForm onSubmit={vi.fn()} />)

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('renders submit button', () => {
    render(<LoginForm onSubmit={vi.fn()} />)

    expect(screen.getByRole('button', { name: /login|sign in/i })).toBeInTheDocument()
  })

  it('validates email format', async () => {
    const user = userEvent.setup()
    render(<LoginForm onSubmit={vi.fn()} />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /login|sign in/i })

    await user.type(emailInput, 'invalid-email')
    await user.type(passwordInput, 'somepassword')
    await user.click(submitButton)

    expect(await screen.findByText(/valid email/i)).toBeInTheDocument()
  })

  it('validates password is not empty', async () => {
    const user = userEvent.setup()
    render(<LoginForm onSubmit={vi.fn()} />)

    const emailInput = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /login|sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.click(submitButton)

    expect(await screen.findByText(/password is required/i)).toBeInTheDocument()
  })

  it('calls onSubmit with form data when validation passes', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<LoginForm onSubmit={onSubmit} />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /login|sign in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      })
    })
  })

  it('displays loading state when isLoading is true', () => {
    render(<LoginForm onSubmit={vi.fn()} isLoading={true} />)

    const submitButton = screen.getByRole('button', { name: /login|sign in|logging/i })
    expect(submitButton).toBeDisabled()
  })

  it('displays error message when error prop is provided', () => {
    const errorMessage = 'Invalid credentials'
    render(<LoginForm onSubmit={vi.fn()} error={errorMessage} />)

    expect(screen.getByText(errorMessage)).toBeInTheDocument()
  })
})
