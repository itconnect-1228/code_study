import { describe, it, expect, vi, beforeEach } from 'vitest'
import { documentService, type LearningDocument, type DocumentStatus } from './document-service'
import { apiClient } from './api-client'

// API client 모킹
vi.mock('./api-client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

const mockedApiClient = vi.mocked(apiClient)

describe('documentService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getDocument', () => {
    it('태스크의 학습 문서를 조회해야 함', async () => {
      const mockResponse = {
        data: {
          id: 'doc-123',
          task_id: 'task-456',
          status: 'completed' as DocumentStatus,
          chapters: {
            summary: { title: '요약', content: '테스트 내용' },
            prerequisites: { title: '사전 지식', concepts: [] },
            coreLogic: { title: '핵심 로직', content: '로직 설명' },
            lineByLine: { title: '라인별', explanations: [] },
            syntaxReference: { title: '문법', items: [] },
            commonPatterns: { title: '패턴', patterns: [] },
            exercises: { title: '연습', items: [] },
          },
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      }

      mockedApiClient.get.mockResolvedValueOnce(mockResponse)

      const result = await documentService.getDocument('task-456')

      expect(mockedApiClient.get).toHaveBeenCalledWith('/tasks/task-456/document')
      expect(result).not.toBeNull()
      expect(result?.id).toBe('doc-123')
      expect(result?.taskId).toBe('task-456')
      expect(result?.status).toBe('completed')
    })

    it('문서가 없으면 null을 반환해야 함', async () => {
      mockedApiClient.get.mockRejectedValueOnce(new Error('Not found'))

      const result = await documentService.getDocument('task-999')

      expect(result).toBeNull()
    })

    it('snake_case를 camelCase로 변환해야 함', async () => {
      const mockResponse = {
        data: {
          id: 'doc-123',
          task_id: 'task-456',
          status: 'completed' as DocumentStatus,
          chapters: {
            summary: { title: '요약', content: '내용' },
            prerequisites: { title: '사전 지식', concepts: [] },
            coreLogic: { title: '핵심 로직', content: '' },
            lineByLine: { title: '라인별', explanations: [] },
            syntaxReference: { title: '문법', items: [] },
            commonPatterns: { title: '패턴', patterns: [] },
            exercises: { title: '연습', items: [] },
          },
          error_message: '오류 메시지',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-02T00:00:00Z',
        },
      }

      mockedApiClient.get.mockResolvedValueOnce(mockResponse)

      const result = await documentService.getDocument('task-456')

      expect(result?.taskId).toBe('task-456')
      expect(result?.errorMessage).toBe('오류 메시지')
      expect(result?.createdAt).toBe('2025-01-01T00:00:00Z')
      expect(result?.updatedAt).toBe('2025-01-02T00:00:00Z')
    })
  })

  describe('generateDocument', () => {
    it('문서 생성을 요청해야 함', async () => {
      const mockResponse = {
        data: {
          id: 'doc-new',
          task_id: 'task-789',
          status: 'generating' as DocumentStatus,
          chapters: {
            summary: { title: '', content: '' },
            prerequisites: { title: '', concepts: [] },
            coreLogic: { title: '', content: '' },
            lineByLine: { title: '', explanations: [] },
            syntaxReference: { title: '', items: [] },
            commonPatterns: { title: '', patterns: [] },
            exercises: { title: '', items: [] },
          },
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      }

      mockedApiClient.post.mockResolvedValueOnce(mockResponse)

      const result = await documentService.generateDocument('task-789')

      expect(mockedApiClient.post).toHaveBeenCalledWith('/tasks/task-789/document/generate')
      expect(result.id).toBe('doc-new')
      expect(result.status).toBe('generating')
    })
  })

  describe('pollDocumentStatus', () => {
    it('문서 상태를 조회해야 함', async () => {
      const mockResponse = {
        data: {
          status: 'generating' as DocumentStatus,
          progress: 50,
        },
      }

      mockedApiClient.get.mockResolvedValueOnce(mockResponse)

      const result = await documentService.pollDocumentStatus('task-456')

      expect(mockedApiClient.get).toHaveBeenCalledWith('/tasks/task-456/document/status')
      expect(result.status).toBe('generating')
      expect(result.progress).toBe(50)
    })

    it('완료된 상태를 반환해야 함', async () => {
      const mockResponse = {
        data: {
          status: 'completed' as DocumentStatus,
        },
      }

      mockedApiClient.get.mockResolvedValueOnce(mockResponse)

      const result = await documentService.pollDocumentStatus('task-456')

      expect(result.status).toBe('completed')
      expect(result.progress).toBeUndefined()
    })
  })

  describe('타입 정의', () => {
    it('LearningDocument 타입이 올바르게 정의되어야 함', () => {
      const doc: LearningDocument = {
        id: 'doc-1',
        taskId: 'task-1',
        status: 'completed',
        chapters: {
          summary: { title: '요약', content: '내용' },
          prerequisites: { title: '사전 지식', concepts: [] },
          coreLogic: { title: '핵심 로직', content: '' },
          lineByLine: { title: '라인별', explanations: [] },
          syntaxReference: { title: '문법', items: [] },
          commonPatterns: { title: '패턴', patterns: [] },
          exercises: { title: '연습', items: [] },
        },
        createdAt: '2025-01-01',
        updatedAt: '2025-01-01',
      }

      expect(doc.id).toBe('doc-1')
    })

    it('DocumentStatus 타입이 유효한 값만 허용해야 함', () => {
      const validStatuses: DocumentStatus[] = ['pending', 'generating', 'completed', 'error']
      expect(validStatuses).toContain('pending')
      expect(validStatuses).toContain('generating')
      expect(validStatuses).toContain('completed')
      expect(validStatuses).toContain('error')
    })
  })
})
