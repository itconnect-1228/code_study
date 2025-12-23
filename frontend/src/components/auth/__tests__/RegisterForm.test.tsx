import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import RegisterForm from '../RegisterForm'

describe('RegisterForm', () => {
  it('renders email, password, and confirm password fields', () => {
    render(<RegisterForm onSubmit={vi.fn()} />)

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
  })

  it('renders submit button', () => {
    render(<RegisterForm onSubmit={vi.fn()} />)

    expect(screen.getByRole('button', { name: /register|sign up/i })).toBeInTheDocument()
  })

  it('validates email format', async () => {
    const user = userEvent.setup()
    render(<RegisterForm onSubmit={vi.fn()} />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const submitButton = screen.getByRole('button', { name: /register|sign up/i })

    // Fill in valid password fields, but invalid email
    await user.type(emailInput, 'invalid-email')
    await user.type(passwordInput, 'validpassword123')
    await user.type(confirmPasswordInput, 'validpassword123')
    await user.click(submitButton)

    expect(await screen.findByText(/valid email/i)).toBeInTheDocument()
  })

  it('validates password minimum length', async () => {
    const user = userEvent.setup()
    render(<RegisterForm onSubmit={vi.fn()} />)

    const passwordInput = screen.getByLabelText(/^password$/i)
    const submitButton = screen.getByRole('button', { name: /register|sign up/i })

    await user.type(passwordInput, '12345')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument()
    })
  })

  it('validates password confirmation matches', async () => {
    const user = userEvent.setup()
    render(<RegisterForm onSubmit={vi.fn()} />)

    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const submitButton = screen.getByRole('button', { name: /register|sign up/i })

    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password456')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
    })
  })

  it('calls onSubmit with form data when validation passes', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<RegisterForm onSubmit={onSubmit} />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const submitButton = screen.getByRole('button', { name: /register|sign up/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')
    await user.click(submitButton)

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      })
    })
  })

  it('displays loading state when isLoading is true', () => {
    render(<RegisterForm onSubmit={vi.fn()} isLoading={true} />)

    const submitButton = screen.getByRole('button', { name: /register|sign up|registering/i })
    expect(submitButton).toBeDisabled()
  })

  it('displays error message when error prop is provided', () => {
    const errorMessage = 'Registration failed'
    render(<RegisterForm onSubmit={vi.fn()} error={errorMessage} />)

    expect(screen.getByText(errorMessage)).toBeInTheDocument()
  })
})
