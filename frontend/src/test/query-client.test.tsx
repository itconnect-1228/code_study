import { describe, it, expect } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { queryClient } from '../lib/queryClient'

describe('QueryClient Configuration', () => {
  it('exports queryClient with correct staleTime', () => {
    const defaultOptions = queryClient.getDefaultOptions()
    expect(defaultOptions.queries?.staleTime).toBe(5 * 60 * 1000)
  })

  it('exports queryClient with correct gcTime', () => {
    const defaultOptions = queryClient.getDefaultOptions()
    expect(defaultOptions.queries?.gcTime).toBe(10 * 60 * 1000)
  })

  it('exports queryClient with correct retry count', () => {
    const defaultOptions = queryClient.getDefaultOptions()
    expect(defaultOptions.queries?.retry).toBe(3)
  })

  it('exports queryClient with refetchOnWindowFocus disabled', () => {
    const defaultOptions = queryClient.getDefaultOptions()
    expect(defaultOptions.queries?.refetchOnWindowFocus).toBe(false)
  })
})

describe('QueryClient Integration', () => {
  const createTestQueryClient = () =>
    new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 5 * 60 * 1000,
          gcTime: 10 * 60 * 1000,
          retry: false,
          refetchOnWindowFocus: false,
        },
      },
    })

  const TestComponent = () => {
    const { data, isLoading, isSuccess } = useQuery({
      queryKey: ['test'],
      queryFn: async () => {
        return { message: 'Hello, TanStack Query!' }
      },
    })

    if (isLoading) return <div>Loading...</div>
    if (isSuccess) return <div>{data.message}</div>
    return null
  }

  it('useQuery hook works with QueryClientProvider', async () => {
    const testClient = createTestQueryClient()

    render(
      <QueryClientProvider client={testClient}>
        <TestComponent />
      </QueryClientProvider>
    )

    expect(screen.getByText('Loading...')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Hello, TanStack Query!')).toBeInTheDocument()
    })
  })

  it('caches query results', async () => {
    const testClient = createTestQueryClient()
    let callCount = 0

    const CachingTestComponent = () => {
      const { data, isSuccess } = useQuery({
        queryKey: ['cache-test'],
        queryFn: async () => {
          callCount++
          return { count: callCount }
        },
      })

      if (isSuccess) return <div>Count: {data.count}</div>
      return <div>Loading...</div>
    }

    const { rerender } = render(
      <QueryClientProvider client={testClient}>
        <CachingTestComponent />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('Count: 1')).toBeInTheDocument()
    })

    // Rerender should use cached result
    rerender(
      <QueryClientProvider client={testClient}>
        <CachingTestComponent />
      </QueryClientProvider>
    )

    expect(screen.getByText('Count: 1')).toBeInTheDocument()
    expect(callCount).toBe(1)
  })

  it('handles query errors gracefully', async () => {
    const testClient = createTestQueryClient()

    const ErrorTestComponent = () => {
      const { error, isError } = useQuery({
        queryKey: ['error-test'],
        queryFn: async () => {
          throw new Error('Test error')
        },
      })

      if (isError) return <div>Error: {(error as Error).message}</div>
      return <div>Loading...</div>
    }

    render(
      <QueryClientProvider client={testClient}>
        <ErrorTestComponent />
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('Error: Test error')).toBeInTheDocument()
    })
  })
})
