import { apiClient } from './api-client'

/**
 * Backend task response format (snake_case)
 */
interface TaskResponseDTO {
  id: string
  project_id: string
  task_number: number
  title: string
  description: string | null
  upload_method: 'file' | 'folder' | 'paste' | null
  deletion_status: string
  created_at: string
  updated_at: string
}

interface TaskListResponseDTO {
  tasks: TaskResponseDTO[]
  total: number
}

interface CodeFileResponseDTO {
  id: string
  filename: string
  relative_path: string
  content: string
  language: string
  line_count: number
  size_bytes: number
}

interface CodeFilesResponseDTO {
  files: CodeFileResponseDTO[]
  total: number
}

/**
 * Frontend task format (camelCase)
 */
export interface Task {
  id: string
  projectId: string
  taskNumber: number
  title: string
  description: string | null
  uploadMethod: 'file' | 'folder' | 'paste' | null
  deletionStatus: string
  createdAt: string
  updatedAt: string
}

export interface TaskListResponse {
  tasks: Task[]
  total: number
}

export interface CodeFile {
  id: string
  filename: string
  relativePath: string
  content: string
  language: string
  lineCount: number
  sizeBytes: number
}

export interface CodeFilesResponse {
  files: CodeFile[]
  total: number
}

/**
 * Data for creating a new task
 */
export interface TaskCreateData {
  title: string
  uploadType: 'file' | 'folder' | 'paste'
  files?: File[]
  code?: string
  language?: string
}

/**
 * Transform backend task format to frontend format
 */
const transformTask = (dto: TaskResponseDTO): Task => ({
  id: dto.id,
  projectId: dto.project_id,
  taskNumber: dto.task_number,
  title: dto.title,
  description: dto.description,
  uploadMethod: dto.upload_method,
  deletionStatus: dto.deletion_status,
  createdAt: dto.created_at,
  updatedAt: dto.updated_at,
})

/**
 * Transform backend code file format to frontend format
 */
const transformCodeFile = (dto: CodeFileResponseDTO): CodeFile => ({
  id: dto.id,
  filename: dto.filename,
  relativePath: dto.relative_path,
  content: dto.content,
  language: dto.language,
  lineCount: dto.line_count,
  sizeBytes: dto.size_bytes,
})

/**
 * Task service - handles all task-related API calls
 */
export const taskService = {
  /**
   * Get all tasks for a project
   * @param projectId - Project ID
   * @returns List of tasks
   */
  async getTasks(projectId: string): Promise<TaskListResponse> {
    const response = await apiClient.get<TaskListResponseDTO>(`/projects/${projectId}/tasks`)

    return {
      tasks: response.data.tasks.map(transformTask),
      total: response.data.total,
    }
  },

  /**
   * Get a single task by ID
   * @param taskId - Task ID
   * @returns Task data
   */
  async getTask(taskId: string): Promise<Task> {
    const response = await apiClient.get<TaskResponseDTO>(`/tasks/${taskId}`)

    return transformTask(response.data)
  },

  /**
   * Create a new task with code upload
   * @param projectId - Project ID
   * @param data - Task creation data including files or pasted code
   * @returns Created task
   */
  async createTask(projectId: string, data: TaskCreateData): Promise<Task> {
    const formData = new FormData()
    formData.append('title', data.title)
    formData.append('upload_type', data.uploadType)

    if (data.uploadType === 'paste') {
      if (data.code) {
        formData.append('code', data.code)
      }
      if (data.language) {
        formData.append('language', data.language)
      }
    } else if (data.files) {
      data.files.forEach((file) => {
        formData.append('files', file)
      })
    }

    const response = await apiClient.post<TaskResponseDTO>(
      `/projects/${projectId}/tasks`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )

    return transformTask(response.data)
  },

  /**
   * Update a task
   * @param taskId - Task ID
   * @param data - Fields to update
   * @returns Updated task
   */
  async updateTask(taskId: string, data: { title?: string }): Promise<Task> {
    const response = await apiClient.patch<TaskResponseDTO>(`/tasks/${taskId}`, data)

    return transformTask(response.data)
  },

  /**
   * Delete a task (soft delete)
   * @param taskId - Task ID
   */
  async deleteTask(taskId: string): Promise<void> {
    await apiClient.delete(`/tasks/${taskId}`)
  },

  /**
   * Get code files for a task
   * @param taskId - Task ID
   * @returns Code files with content
   */
  async getTaskCode(taskId: string): Promise<CodeFilesResponse> {
    const response = await apiClient.get<CodeFilesResponseDTO>(`/tasks/${taskId}/code`)

    return {
      files: response.data.files.map(transformCodeFile),
      total: response.data.total,
    }
  },
}

export default taskService
