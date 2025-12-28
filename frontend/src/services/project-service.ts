import { apiClient } from "./api-client";

/**
 * Backend project response format (snake_case)
 */
interface ProjectResponseDTO {
  id: string;
  title: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  last_activity_at: string;
  deletion_status: string;
  trashed_at: string | null;
}

interface ProjectListResponseDTO {
  projects: ProjectResponseDTO[];
  total: number;
}

/**
 * Frontend project format (camelCase)
 */
export interface Project {
  id: string;
  title: string;
  description: string | null;
  createdAt: string;
  updatedAt: string;
  lastActivityAt: string;
  deletionStatus: string;
  trashedAt: string | null;
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
}

/**
 * Transform backend project format to frontend format
 */
const transformProject = (dto: ProjectResponseDTO): Project => ({
  id: dto.id,
  title: dto.title,
  description: dto.description,
  createdAt: dto.created_at,
  updatedAt: dto.updated_at,
  lastActivityAt: dto.last_activity_at,
  deletionStatus: dto.deletion_status,
  trashedAt: dto.trashed_at,
});

/**
 * Project service - handles all project-related API calls
 */
export const projectService = {
  /**
   * Get all projects for the current user
   * @param includeTrashed - Include trashed projects
   * @returns List of projects
   */
  async getProjects(includeTrashed = false): Promise<ProjectListResponse> {
    const params = includeTrashed ? { include_trashed: true } : {};
    const response = await apiClient.get<ProjectListResponseDTO>("/projects", {
      params,
    });

    return {
      projects: response.data.projects.map(transformProject),
      total: response.data.total,
    };
  },

  /**
   * Get a single project by ID
   * @param id - Project ID
   * @returns Project data
   */
  async getProject(id: string): Promise<Project> {
    const response = await apiClient.get<ProjectResponseDTO>(`/projects/${id}`);

    return transformProject(response.data);
  },

  /**
   * Create a new project
   * @param title - Project title
   * @param description - Optional project description
   * @returns Created project
   */
  async createProject(title: string, description?: string): Promise<Project> {
    const body: { title: string; description?: string } = { title };
    if (description) {
      body.description = description;
    }

    const response = await apiClient.post<ProjectResponseDTO>(
      "/projects",
      body,
    );

    return transformProject(response.data);
  },

  /**
   * Update a project
   * @param id - Project ID
   * @param data - Fields to update
   * @returns Updated project
   */
  async updateProject(
    id: string,
    data: { title?: string; description?: string },
  ): Promise<Project> {
    const response = await apiClient.patch<ProjectResponseDTO>(
      `/projects/${id}`,
      data,
    );

    return transformProject(response.data);
  },

  /**
   * Delete a project (soft delete)
   * @param id - Project ID
   */
  async deleteProject(id: string): Promise<void> {
    await apiClient.delete(`/projects/${id}`);
  },

  /**
   * Restore a project from trash
   * @param id - Project ID
   * @returns Restored project
   */
  async restoreProject(id: string): Promise<Project> {
    const response = await apiClient.post<ProjectResponseDTO>(
      `/projects/${id}/restore`,
    );

    return transformProject(response.data);
  },

  /**
   * Permanently delete a project from trash
   * @param id - Project ID
   */
  async permanentDeleteProject(id: string): Promise<void> {
    await apiClient.delete(`/projects/${id}/permanent`);
  },
};

export default projectService;
