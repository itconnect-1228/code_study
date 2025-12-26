# T097: GET /tasks/{task_id}/document API 엔드포인트 구현

**완료일**: 2025-12-26
**담당**: AI Code Learning Platform
**상태**: 완료

## 무엇을 만들었나요?

Task에 대한 학습 문서를 조회하는 REST API 엔드포인트를 구현했습니다. 사용자가 코드를 업로드하면 AI가 생성한 7장 구성의 학습 문서를 가져올 수 있습니다.

## 왜 이렇게 만들었나요?

프론트엔드에서 학습 문서 내용을 표시하려면 백엔드에서 문서를 제공하는 API가 필요합니다. 이 엔드포인트는:

1. **인증 필수**: 로그인한 사용자만 접근 가능
2. **소유권 검증**: 본인이 만든 Task의 문서만 조회 가능
3. **보안**: 다른 사용자의 Task에 접근하면 404 반환 (존재 여부 숨김)

## 어떻게 작동하나요?

```
GET /api/v1/tasks/{task_id}/document
```

1. **인증 확인**: 쿠키에서 JWT 토큰 검증
2. **소유권 검증**: Task가 현재 사용자의 것인지 확인
3. **문서 조회**: DocumentGenerationService를 통해 문서 가져오기
4. **응답 반환**: DocumentResponse 스키마로 반환

### 응답 예시

```json
{
  "id": "uuid-string",
  "task_id": "uuid-string",
  "generation_status": "completed",
  "content": {
    "chapter1": {"title": "What This Code Does", "summary": "..."},
    "chapter2": {"title": "Prerequisites", "concepts": [...]},
    ...
  },
  "generation_started_at": "2025-12-26T10:00:00Z",
  "generation_completed_at": "2025-12-26T10:02:00Z",
  "created_at": "2025-12-26T10:00:00Z",
  "updated_at": "2025-12-26T10:02:00Z"
}
```

## TDD 방식으로 개발했습니다

### RED Phase (실패하는 테스트 작성)
- 7개의 테스트 케이스 작성
- 인증 필요, Task 소유권 검증, 문서 존재 여부 등

### GREEN Phase (최소 구현)
- `backend/src/api/documents.py` 생성
- router에 documents_router 등록

### REFACTOR Phase (코드 개선)
- ruff로 import 정렬
- 14개 테스트 모두 통과 확인

## 테스트 케이스

1. `test_get_document_requires_authentication` - 인증 없이 접근하면 401
2. `test_get_document_task_not_found` - 없는 Task ID로 접근하면 404
3. `test_get_document_forbidden_for_other_user` - 다른 사용자의 Task 접근하면 404
4. `test_get_document_not_found_when_no_document` - 문서가 없으면 404
5. `test_get_document_success_with_completed_document` - 완료된 문서 정상 조회
6. `test_get_document_returns_pending_document` - 진행 중인 문서도 조회 가능

## 수정한 파일들

**새로 만든 파일:**
- `backend/src/api/documents.py` - Document API 엔드포인트
- `backend/tests/unit/api/test_documents.py` - 테스트 코드

**수정한 파일:**
- `backend/src/api/router.py` - documents_router 등록

## 관련 요구사항

- FR-021: AI 통합 문서 생성
- FR-026~034: 7장 문서 구조
- 인증 및 권한 관리

## 다음 단계

- T098: 문서 생성 상태 조회 API (동일 파일에 구현 완료)
- 프론트엔드 문서 뷰어 컴포넌트 개발
