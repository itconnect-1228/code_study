import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import RegisterForm from '@/components/auth/RegisterForm'
import { authService } from '@/services/auth-service'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function Register() {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | undefined>()

  const handleSubmit = async (data: { email: string; password: string }) => {
    setIsLoading(true)
    setError(undefined)

    try {
      await authService.register(data.email, data.password)
      navigate('/login', { state: { message: 'Registration successful. Please login.' } })
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string } } }
      const message = errorObj.response?.data?.detail || 'Registration failed. Please try again.'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Create Account</CardTitle>
          <CardDescription>Enter your details to create a new account</CardDescription>
        </CardHeader>
        <CardContent>
          <RegisterForm onSubmit={handleSubmit} isLoading={isLoading} error={error} />
          <div className="mt-4 text-center text-sm">
            Already have an account?{' '}
            <Link to="/login" className="text-blue-600 hover:underline">
              Login
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
