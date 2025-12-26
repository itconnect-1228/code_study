import { apiClient } from './api-client'

/**
 * 학습 문서 상태
 */
export type DocumentStatus = 'pending' | 'generating' | 'completed' | 'error'

/**
 * 개념 카드 (사전 지식 챕터용)
 */
export interface ConceptCard {
  name: string
  explanation: string
  analogy: string
}

/**
 * 라인별 설명 항목
 */
export interface LineExplanation {
  lineNumber: number
  code: string
  explanation: string
}

/**
 * 문법 레퍼런스 항목
 */
export interface SyntaxItem {
  syntax: string
  description: string
}

/**
 * 코드 패턴 항목
 */
export interface PatternItem {
  name: string
  description: string
}

/**
 * 연습 문제 항목
 */
export interface ExerciseItem {
  question: string
  hint: string
}

/**
 * 학습 문서 챕터들
 */
export interface DocumentChapters {
  /** Chapter 1: 코드 요약 */
  summary: {
    title: string
    content: string
  }
  /** Chapter 2: 사전 지식 */
  prerequisites: {
    title: string
    concepts: ConceptCard[]
  }
  /** Chapter 3: 핵심 로직 */
  coreLogic: {
    title: string
    content: string
  }
  /** Chapter 4: 라인별 설명 */
  lineByLine: {
    title: string
    explanations: LineExplanation[]
  }
  /** Chapter 5: 문법 레퍼런스 */
  syntaxReference: {
    title: string
    items: SyntaxItem[]
  }
  /** Chapter 6: 자주 쓰는 패턴 */
  commonPatterns: {
    title: string
    patterns: PatternItem[]
  }
  /** Chapter 7: 연습 문제 */
  exercises: {
    title: string
    items: ExerciseItem[]
  }
}

/**
 * 학습 문서 (Frontend 형식 - camelCase)
 */
export interface LearningDocument {
  id: string
  taskId: string
  status: DocumentStatus
  chapters: DocumentChapters
  errorMessage?: string
  createdAt: string
  updatedAt: string
}

/**
 * Backend 응답 형식 (snake_case)
 */
interface DocumentResponseDTO {
  id: string
  task_id: string
  status: DocumentStatus
  chapters: DocumentChapters
  error_message?: string
  created_at: string
  updated_at: string
}

/**
 * Backend 응답을 Frontend 형식으로 변환
 */
const transformDocument = (dto: DocumentResponseDTO): LearningDocument => ({
  id: dto.id,
  taskId: dto.task_id,
  status: dto.status,
  chapters: dto.chapters,
  errorMessage: dto.error_message,
  createdAt: dto.created_at,
  updatedAt: dto.updated_at,
})

/**
 * Document Service - 학습 문서 API 호출 관리
 */
export const documentService = {
  /**
   * 태스크의 학습 문서 조회
   * @param taskId - 태스크 ID
   * @returns 학습 문서 또는 null (없는 경우)
   */
  async getDocument(taskId: string): Promise<LearningDocument | null> {
    try {
      const response = await apiClient.get<DocumentResponseDTO>(`/tasks/${taskId}/document`)
      return transformDocument(response.data)
    } catch (error) {
      // 문서가 없는 경우 null 반환
      return null
    }
  },

  /**
   * 문서 생성 요청
   * @param taskId - 태스크 ID
   * @returns 생성된 문서 정보
   */
  async generateDocument(taskId: string): Promise<LearningDocument> {
    const response = await apiClient.post<DocumentResponseDTO>(`/tasks/${taskId}/document/generate`)
    return transformDocument(response.data)
  },

  /**
   * 문서 상태 폴링 (생성 중인 경우)
   * @param taskId - 태스크 ID
   * @returns 현재 문서 상태
   */
  async pollDocumentStatus(taskId: string): Promise<{ status: DocumentStatus; progress?: number }> {
    const response = await apiClient.get<{ status: DocumentStatus; progress?: number }>(
      `/tasks/${taskId}/document/status`
    )
    return response.data
  },
}

export default documentService
