# T098: GET /tasks/{task_id}/document/status API 엔드포인트 구현

**완료일**: 2025-12-26
**담당**: AI Code Learning Platform
**상태**: 완료

## 무엇을 만들었나요?

문서 생성 상태를 조회하는 REST API 엔드포인트를 구현했습니다. AI가 학습 문서를 생성하는 동안 프론트엔드에서 진행 상황을 폴링(polling)하는 데 사용됩니다.

## 왜 이렇게 만들었나요?

AI 문서 생성은 시간이 걸리는 작업입니다 (목표: 500 LOC당 3분 이내). 사용자에게 진행 상황을 보여주려면:

1. **경량 API**: 전체 문서 내용 없이 상태만 빠르게 조회
2. **예상 시간**: 남은 시간 추정치 제공 (in_progress 상태일 때)
3. **오류 정보**: 생성 실패 시 에러 메시지 제공

## 어떻게 작동하나요?

```
GET /api/v1/tasks/{task_id}/document/status
```

### 상태 종류

| 상태 | 설명 |
|------|------|
| `not_found` | 문서가 아직 생성되지 않음 |
| `pending` | 생성 대기 중 |
| `in_progress` | 현재 생성 중 (estimated_time_remaining 포함) |
| `completed` | 생성 완료 |
| `failed` | 생성 실패 (error 메시지 포함) |

### 응답 예시

```json
{
  "status": "in_progress",
  "started_at": "2025-12-26T10:00:00Z",
  "completed_at": null,
  "error": null,
  "estimated_time_remaining": 120
}
```

## TDD 방식으로 개발했습니다

### RED Phase (실패하는 테스트 작성)
- 7개의 테스트 케이스 작성
- 각 상태별 응답 검증

### GREEN Phase (최소 구현)
- `get_document_status` 엔드포인트 구현
- DocumentGenerationService의 기존 `get_generation_status` 메서드 활용

### REFACTOR Phase (코드 개선)
- import 정렬
- 전체 14개 테스트 통과 확인

## 테스트 케이스

1. `test_get_document_status_requires_authentication` - 인증 필요
2. `test_get_document_status_task_not_found` - 없는 Task면 404
3. `test_get_document_status_forbidden_for_other_user` - 다른 사용자면 404
4. `test_get_document_status_not_found_when_no_document` - 문서 없으면 not_found 상태
5. `test_get_document_status_pending` - pending 상태 응답
6. `test_get_document_status_in_progress` - in_progress 상태 + estimated_time_remaining
7. `test_get_document_status_completed` - completed 상태 응답
8. `test_get_document_status_failed` - failed 상태 + error 메시지

## 수정한 파일들

**동일 파일에 구현 (T097과 함께):**
- `backend/src/api/documents.py` - Document API 엔드포인트
- `backend/tests/unit/api/test_documents.py` - 테스트 코드

## 관련 요구사항

- FR-083: 성능 목표 (500 LOC당 3분 이내)
- FR-088~094: 재시도 로직 및 상태 추적

## 사용 예시 (프론트엔드)

```typescript
// 문서 생성 상태 폴링 예시
const pollStatus = async (taskId: string) => {
  const response = await fetch(`/api/v1/tasks/${taskId}/document/status`);
  const data = await response.json();
  
  if (data.status === 'completed') {
    // 전체 문서 로드
    fetchDocument(taskId);
  } else if (data.status === 'in_progress') {
    // 진행률 표시
    showProgress(data.estimated_time_remaining);
    setTimeout(() => pollStatus(taskId), 3000);
  } else if (data.status === 'failed') {
    // 오류 표시
    showError(data.error);
  }
};
```

## 다음 단계

- 프론트엔드 문서 생성 상태 UI 컴포넌트
- 진행률 표시 기능
