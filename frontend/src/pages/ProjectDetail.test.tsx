import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ProjectDetail from './ProjectDetail'

// Mock pointer capture methods for Radix UI
beforeEach(() => {
  Element.prototype.hasPointerCapture = vi.fn(() => false)
  Element.prototype.setPointerCapture = vi.fn()
  Element.prototype.releasePointerCapture = vi.fn()
})

// Mock project service
vi.mock('@/services/project-service', () => ({
  projectService: {
    getProject: vi.fn(),
    updateProject: vi.fn(),
    deleteProject: vi.fn(),
  },
}))

// Mock task service
vi.mock('@/services/task-service', () => ({
  taskService: {
    getTasks: vi.fn(),
    createTask: vi.fn(),
  },
}))

// Import mocked modules
import { projectService } from '@/services/project-service'
import { taskService } from '@/services/task-service'

const mockProject = {
  id: 'project-123',
  title: 'Test Project',
  description: 'Test description',
  createdAt: '2025-01-15T10:00:00Z',
  updatedAt: '2025-01-15T10:00:00Z',
  lastActivityAt: '2025-01-15T12:00:00Z',
  deletionStatus: 'active',
  trashedAt: null,
}

const mockTasks = [
  {
    id: 'task-1',
    taskNumber: 1,
    title: 'First Task',
    status: 'completed' as const,
    codeLanguage: 'javascript',
    uploadType: 'file' as const,
    createdAt: '2025-01-15T10:30:00Z',
    updatedAt: '2025-01-15T10:30:00Z',
  },
  {
    id: 'task-2',
    taskNumber: 2,
    title: 'Second Task',
    status: 'generating' as const,
    codeLanguage: 'python',
    uploadType: 'paste' as const,
    createdAt: '2025-01-15T11:00:00Z',
    updatedAt: '2025-01-15T11:00:00Z',
  },
]

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

const renderWithProviders = (projectId: string = 'project-123') => {
  const queryClient = createQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/projects/:id" element={<ProjectDetail />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>,
    {
      wrapper: ({ children }) => {
        // Set the route
        window.history.pushState({}, '', `/projects/${projectId}`)
        return <>{children}</>
      },
    }
  )
}

describe('ProjectDetail with Tasks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(projectService.getProject as ReturnType<typeof vi.fn>).mockResolvedValue(mockProject)
    ;(taskService.getTasks as ReturnType<typeof vi.fn>).mockResolvedValue({
      tasks: mockTasks,
      total: 2,
    })
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('task list display', () => {
    it('displays task count in stats card', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText('2개')).toBeInTheDocument()
      })
    })

    it('displays task timeline with tasks', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText('First Task')).toBeInTheDocument()
        expect(screen.getByText('Second Task')).toBeInTheDocument()
      })
    })

    it('shows task numbers', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText(/Task 1/i)).toBeInTheDocument()
        expect(screen.getByText(/Task 2/i)).toBeInTheDocument()
      })
    })

    it('shows task status badges', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText(/완료/i)).toBeInTheDocument()
        expect(screen.getByText(/생성중/i)).toBeInTheDocument()
      })
    })

    it('shows language badges', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText(/javascript/i)).toBeInTheDocument()
        expect(screen.getByText(/python/i)).toBeInTheDocument()
      })
    })
  })

  describe('empty task state', () => {
    beforeEach(() => {
      ;(taskService.getTasks as ReturnType<typeof vi.fn>).mockResolvedValue({
        tasks: [],
        total: 0,
      })
    })

    it('shows empty state message when no tasks', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText(/아직 태스크가 없습니다/i)).toBeInTheDocument()
      })
    })

    it('shows 0개 in task count', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText('0개')).toBeInTheDocument()
      })
    })
  })

  describe('task creation', () => {
    it('renders create task button', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /새 태스크/i })).toBeInTheDocument()
      })
    })

    it('opens create task modal when button clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /새 태스크/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /새 태스크/i }))

      await waitFor(() => {
        expect(screen.getByText(/새 태스크 만들기/i)).toBeInTheDocument()
      })
    })

    it('creates task and refreshes list on submit', async () => {
      const user = userEvent.setup()
      const newTask = {
        id: 'task-3',
        taskNumber: 3,
        title: 'New Task',
        status: 'pending' as const,
        codeLanguage: 'javascript',
        uploadType: 'file' as const,
        createdAt: '2025-01-15T12:00:00Z',
        updatedAt: '2025-01-15T12:00:00Z',
      }

      ;(taskService.createTask as ReturnType<typeof vi.fn>).mockResolvedValue(newTask)

      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /새 태스크/i })).toBeInTheDocument()
      })

      // Open modal
      await user.click(screen.getByRole('button', { name: /새 태스크/i }))

      await waitFor(() => {
        expect(screen.getByLabelText(/태스크 제목/i)).toBeInTheDocument()
      })

      // Fill in title
      const titleInput = screen.getByLabelText(/태스크 제목/i)
      await user.type(titleInput, 'New Task')

      // Add a file via drag and drop
      const dropZone = screen.getByTestId('file-drop-zone')
      const file = new File(['test content'], 'test.js', { type: 'text/javascript' })
      fireEvent.drop(dropZone, {
        dataTransfer: {
          files: [file],
          types: ['Files'],
        },
      })

      await waitFor(() => {
        expect(screen.getByText(/1개 파일/i)).toBeInTheDocument()
      })

      // Submit
      const submitButton = screen.getByRole('button', { name: /태스크 만들기/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(taskService.createTask).toHaveBeenCalledWith('project-123', expect.objectContaining({
          title: 'New Task',
          uploadType: 'file',
        }))
      })
    })
  })

  describe('task navigation', () => {
    it('task cards are links to task detail page', async () => {
      renderWithProviders()

      await waitFor(() => {
        expect(screen.getByText('First Task')).toBeInTheDocument()
      })

      const taskLink = screen.getByRole('link', { name: /Task 1/i })
      expect(taskLink).toHaveAttribute('href', '/tasks/task-1')
    })
  })

  describe('loading state', () => {
    it('shows loading skeleton while fetching tasks', async () => {
      // Delay the response
      ;(taskService.getTasks as ReturnType<typeof vi.fn>).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ tasks: mockTasks, total: 2 }), 100))
      )

      renderWithProviders()

      // Should show loading state initially
      expect(screen.queryByText('First Task')).not.toBeInTheDocument()

      // After loading, tasks should appear
      await waitFor(() => {
        expect(screen.getByText('First Task')).toBeInTheDocument()
      })
    })
  })
})
