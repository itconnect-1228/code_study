import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { taskService, type Task, type TaskCreateData } from './task-service'
import { apiClient } from './api-client'

// Mock the api-client module
vi.mock('./api-client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('taskService', () => {
  const mockApiClient = apiClient as {
    get: ReturnType<typeof vi.fn>
    post: ReturnType<typeof vi.fn>
    patch: ReturnType<typeof vi.fn>
    delete: ReturnType<typeof vi.fn>
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('getTasks', () => {
    it('fetches tasks for a project', async () => {
      const mockResponse = {
        data: {
          tasks: [
            {
              id: 'task-1',
              task_number: 1,
              title: 'First Task',
              status: 'completed',
              code_language: 'javascript',
              upload_type: 'file',
              created_at: '2025-01-15T10:30:00Z',
              updated_at: '2025-01-15T11:00:00Z',
            },
          ],
          total: 1,
        },
      }

      mockApiClient.get.mockResolvedValue(mockResponse)

      const result = await taskService.getTasks('project-123')

      expect(mockApiClient.get).toHaveBeenCalledWith('/projects/project-123/tasks')
      expect(result.tasks).toHaveLength(1)
      expect(result.tasks[0]).toEqual({
        id: 'task-1',
        taskNumber: 1,
        title: 'First Task',
        status: 'completed',
        codeLanguage: 'javascript',
        uploadType: 'file',
        createdAt: '2025-01-15T10:30:00Z',
        updatedAt: '2025-01-15T11:00:00Z',
      })
      expect(result.total).toBe(1)
    })

    it('transforms snake_case to camelCase', async () => {
      const mockResponse = {
        data: {
          tasks: [
            {
              id: 'task-1',
              task_number: 5,
              title: 'Test',
              status: 'pending',
              code_language: 'python',
              upload_type: 'folder',
              created_at: '2025-01-15T10:30:00Z',
              updated_at: '2025-01-15T10:30:00Z',
            },
          ],
          total: 1,
        },
      }

      mockApiClient.get.mockResolvedValue(mockResponse)

      const result = await taskService.getTasks('project-123')

      expect(result.tasks[0].taskNumber).toBe(5)
      expect(result.tasks[0].codeLanguage).toBe('python')
      expect(result.tasks[0].uploadType).toBe('folder')
      expect(result.tasks[0].createdAt).toBe('2025-01-15T10:30:00Z')
      expect(result.tasks[0].updatedAt).toBe('2025-01-15T10:30:00Z')
    })
  })

  describe('getTask', () => {
    it('fetches a single task by ID', async () => {
      const mockResponse = {
        data: {
          id: 'task-1',
          task_number: 1,
          title: 'Single Task',
          status: 'generating',
          code_language: 'typescript',
          upload_type: 'paste',
          created_at: '2025-01-15T10:30:00Z',
          updated_at: '2025-01-15T10:30:00Z',
        },
      }

      mockApiClient.get.mockResolvedValue(mockResponse)

      const result = await taskService.getTask('task-1')

      expect(mockApiClient.get).toHaveBeenCalledWith('/tasks/task-1')
      expect(result.id).toBe('task-1')
      expect(result.status).toBe('generating')
    })
  })

  describe('createTask', () => {
    it('creates a task with file upload', async () => {
      const mockResponse = {
        data: {
          id: 'task-new',
          task_number: 2,
          title: 'New Task',
          status: 'pending',
          code_language: 'javascript',
          upload_type: 'file',
          created_at: '2025-01-15T10:30:00Z',
          updated_at: '2025-01-15T10:30:00Z',
        },
      }

      mockApiClient.post.mockResolvedValue(mockResponse)

      const file = new File(['console.log("hello")'], 'test.js', { type: 'text/javascript' })
      const taskData: TaskCreateData = {
        title: 'New Task',
        uploadType: 'file',
        files: [file],
      }

      const result = await taskService.createTask('project-123', taskData)

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/projects/project-123/tasks',
        expect.any(FormData),
        expect.objectContaining({
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      )
      expect(result.id).toBe('task-new')
      expect(result.taskNumber).toBe(2)
    })

    it('creates a task with folder upload', async () => {
      const mockResponse = {
        data: {
          id: 'task-folder',
          task_number: 3,
          title: 'Folder Task',
          status: 'pending',
          code_language: 'javascript',
          upload_type: 'folder',
          created_at: '2025-01-15T10:30:00Z',
          updated_at: '2025-01-15T10:30:00Z',
        },
      }

      mockApiClient.post.mockResolvedValue(mockResponse)

      const files = [
        new File(['const a = 1'], 'src/index.js', { type: 'text/javascript' }),
        new File(['const b = 2'], 'src/utils.js', { type: 'text/javascript' }),
      ]
      const taskData: TaskCreateData = {
        title: 'Folder Task',
        uploadType: 'folder',
        files,
      }

      const result = await taskService.createTask('project-123', taskData)

      expect(mockApiClient.post).toHaveBeenCalled()
      expect(result.uploadType).toBe('folder')
    })

    it('creates a task with pasted code', async () => {
      const mockResponse = {
        data: {
          id: 'task-paste',
          task_number: 4,
          title: 'Paste Task',
          status: 'pending',
          code_language: 'python',
          upload_type: 'paste',
          created_at: '2025-01-15T10:30:00Z',
          updated_at: '2025-01-15T10:30:00Z',
        },
      }

      mockApiClient.post.mockResolvedValue(mockResponse)

      const taskData: TaskCreateData = {
        title: 'Paste Task',
        uploadType: 'paste',
        code: 'def hello():\n    print("Hello")',
        language: 'python',
      }

      const result = await taskService.createTask('project-123', taskData)

      expect(mockApiClient.post).toHaveBeenCalled()
      expect(result.codeLanguage).toBe('python')
    })

    it('includes FormData with correct fields for file upload', async () => {
      const mockResponse = {
        data: {
          id: 'task-1',
          task_number: 1,
          title: 'Test',
          status: 'pending',
          code_language: 'javascript',
          upload_type: 'file',
          created_at: '2025-01-15T10:30:00Z',
          updated_at: '2025-01-15T10:30:00Z',
        },
      }

      mockApiClient.post.mockResolvedValue(mockResponse)

      const file = new File(['test'], 'test.js')
      await taskService.createTask('project-123', {
        title: 'Test',
        uploadType: 'file',
        files: [file],
      })

      const formData = mockApiClient.post.mock.calls[0][1] as FormData
      expect(formData.get('title')).toBe('Test')
      expect(formData.get('upload_type')).toBe('file')
      expect(formData.get('files')).toBeTruthy()
    })

    it('includes code and language for paste upload', async () => {
      const mockResponse = {
        data: {
          id: 'task-1',
          task_number: 1,
          title: 'Test',
          status: 'pending',
          code_language: 'python',
          upload_type: 'paste',
          created_at: '2025-01-15T10:30:00Z',
          updated_at: '2025-01-15T10:30:00Z',
        },
      }

      mockApiClient.post.mockResolvedValue(mockResponse)

      await taskService.createTask('project-123', {
        title: 'Test',
        uploadType: 'paste',
        code: 'print("hello")',
        language: 'python',
      })

      const formData = mockApiClient.post.mock.calls[0][1] as FormData
      expect(formData.get('code')).toBe('print("hello")')
      expect(formData.get('language')).toBe('python')
    })
  })

  describe('updateTask', () => {
    it('updates a task title', async () => {
      const mockResponse = {
        data: {
          id: 'task-1',
          task_number: 1,
          title: 'Updated Title',
          status: 'completed',
          code_language: 'javascript',
          upload_type: 'file',
          created_at: '2025-01-15T10:30:00Z',
          updated_at: '2025-01-15T12:00:00Z',
        },
      }

      mockApiClient.patch.mockResolvedValue(mockResponse)

      const result = await taskService.updateTask('task-1', { title: 'Updated Title' })

      expect(mockApiClient.patch).toHaveBeenCalledWith('/tasks/task-1', { title: 'Updated Title' })
      expect(result.title).toBe('Updated Title')
    })
  })

  describe('deleteTask', () => {
    it('soft deletes a task', async () => {
      mockApiClient.delete.mockResolvedValue({ data: {} })

      await taskService.deleteTask('task-1')

      expect(mockApiClient.delete).toHaveBeenCalledWith('/tasks/task-1')
    })
  })

  describe('getTaskCode', () => {
    it('fetches code files for a task', async () => {
      const mockResponse = {
        data: {
          files: [
            {
              id: 'file-1',
              filename: 'index.js',
              relative_path: 'src/index.js',
              content: 'console.log("hello")',
              language: 'javascript',
              line_count: 1,
              size_bytes: 21,
            },
          ],
          total: 1,
        },
      }

      mockApiClient.get.mockResolvedValue(mockResponse)

      const result = await taskService.getTaskCode('task-1')

      expect(mockApiClient.get).toHaveBeenCalledWith('/tasks/task-1/code')
      expect(result.files).toHaveLength(1)
      expect(result.files[0]).toEqual({
        id: 'file-1',
        filename: 'index.js',
        relativePath: 'src/index.js',
        content: 'console.log("hello")',
        language: 'javascript',
        lineCount: 1,
        sizeBytes: 21,
      })
    })
  })
})
