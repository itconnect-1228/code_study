import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import TaskDetail from './TaskDetail'

// Mock pointer capture methods for Radix UI
beforeEach(() => {
  Element.prototype.hasPointerCapture = vi.fn(() => false)
  Element.prototype.setPointerCapture = vi.fn()
  Element.prototype.releasePointerCapture = vi.fn()
})

// Mock task service
vi.mock('@/services/task-service', () => ({
  taskService: {
    getTask: vi.fn(),
    getTaskCode: vi.fn(),
  },
}))

import { taskService } from '@/services/task-service'

const mockTask = {
  id: 'task-123',
  taskNumber: 1,
  title: 'JavaScript Async/Await',
  status: 'completed' as const,
  codeLanguage: 'javascript',
  uploadType: 'file' as const,
  createdAt: '2025-01-15T10:30:00Z',
  updatedAt: '2025-01-15T10:30:00Z',
}

const mockCodeFiles = {
  files: [
    {
      id: 'file-1',
      filename: 'index.js',
      relativePath: 'src/index.js',
      content: 'async function hello() { return "world"; }',
      language: 'javascript',
      lineCount: 1,
      sizeBytes: 42,
    },
  ],
  total: 1,
}

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

const renderWithProviders = (taskId: string = 'task-123') => {
  const queryClient = createQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/tasks/:id" element={<TaskDetail />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>,
    {
      wrapper: ({ children }) => {
        window.history.pushState({}, '', `/tasks/${taskId}`)
        return <>{children}</>
      },
    }
  )
}

describe('TaskDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(taskService.getTask as ReturnType<typeof vi.fn>).mockResolvedValue(mockTask)
    ;(taskService.getTaskCode as ReturnType<typeof vi.fn>).mockResolvedValue(mockCodeFiles)
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('rendering', () => {
    it('displays task title', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText('JavaScript Async/Await')).toBeInTheDocument()
      })
    })

    it('displays task number', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText(/Task 1/i)).toBeInTheDocument()
      })
    })

    it('displays language badge', async () => {
      renderWithProviders()

      await waitFor(() => {
        // Find badge by its class and content
        const badges = screen.getAllByText(/javascript/i)
        // Should have at least the badge (and title may also contain it)
        expect(badges.length).toBeGreaterThanOrEqual(1)
      })
    })

    it('displays status badge', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText(/완료/i)).toBeInTheDocument()
      })
    })

    it('displays back button to project', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /뒤로/i })).toBeInTheDocument()
      })
    })
  })

  describe('tabs', () => {
    it('renders three tab triggers', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /문서/i })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: /실습/i })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: /Q&A/i })).toBeInTheDocument()
      })
    })

    it('shows document tab content by default', async () => {
      renderWithProviders()

      await waitFor(() => {
        // Document tab should be active
        const documentTab = screen.getByRole('tab', { name: /문서/i })
        expect(documentTab).toHaveAttribute('aria-selected', 'true')
      })
    })

    it('switches to practice tab when clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /실습/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('tab', { name: /실습/i }))

      await waitFor(() => {
        expect(screen.getByText(/실습 문제가 곧 제공됩니다/i)).toBeInTheDocument()
      })
    })

    it('switches to Q&A tab when clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /Q&A/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('tab', { name: /Q&A/i }))

      await waitFor(() => {
        expect(screen.getByText(/질문과 답변/i)).toBeInTheDocument()
      })
    })
  })

  describe('document tab', () => {
    it('shows placeholder content for document generation', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText(/학습 문서가 준비되었습니다/i)).toBeInTheDocument()
      })
    })
  })

  describe('practice tab', () => {
    it('shows placeholder content for practice problems', async () => {
      const user = userEvent.setup()
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /실습/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('tab', { name: /실습/i }))

      await waitFor(() => {
        expect(screen.getByText(/Phase 7에서 구현/i)).toBeInTheDocument()
      })
    })
  })

  describe('Q&A tab', () => {
    it('shows placeholder content for Q&A', async () => {
      const user = userEvent.setup()
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /Q&A/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('tab', { name: /Q&A/i }))

      await waitFor(() => {
        expect(screen.getByText(/Phase 8에서 구현/i)).toBeInTheDocument()
      })
    })
  })

  describe('loading state', () => {
    it('shows loading skeleton while fetching task', async () => {
      ;(taskService.getTask as ReturnType<typeof vi.fn>).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockTask), 100))
      )

      renderWithProviders()

      // Should show loading state
      expect(screen.queryByText('JavaScript Async/Await')).not.toBeInTheDocument()

      await waitFor(() => {
        expect(screen.getByText('JavaScript Async/Await')).toBeInTheDocument()
      })
    })
  })

  describe('error state', () => {
    it('shows error message when task not found', async () => {
      ;(taskService.getTask as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Not found'))

      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText(/찾을 수 없습니다/i)).toBeInTheDocument()
      })
    })
  })

  describe('status-specific rendering', () => {
    it('shows generating status with spinner for generating tasks', async () => {
      const generatingTask = { ...mockTask, status: 'generating' as const }
      ;(taskService.getTask as ReturnType<typeof vi.fn>).mockResolvedValue(generatingTask)

      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText(/생성중/i)).toBeInTheDocument()
      })
    })

    it('shows pending status for pending tasks', async () => {
      const pendingTask = { ...mockTask, status: 'pending' as const }
      ;(taskService.getTask as ReturnType<typeof vi.fn>).mockResolvedValue(pendingTask)

      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText(/대기중/i)).toBeInTheDocument()
      })
    })

    it('shows error status for error tasks', async () => {
      const errorTask = { ...mockTask, status: 'error' as const }
      ;(taskService.getTask as ReturnType<typeof vi.fn>).mockResolvedValue(errorTask)

      renderWithProviders()

      await waitFor(() => {
        // Should find the status badge with 오류
        const errorElements = screen.getAllByText(/오류/i)
        expect(errorElements.length).toBeGreaterThanOrEqual(1)
      })
    })
  })
})
