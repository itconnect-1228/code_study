# T080: Task Service

## 무엇을 만들었나요?

백엔드 API와 통신해서 태스크 데이터를 주고받는 서비스 모듈을 만들었어요. 마치 우체부처럼, 프론트엔드에서 필요한 데이터를 백엔드에 요청하고 받아오는 역할을 해요.

## 왜 이렇게 만들었나요?

API 호출 로직을 한 곳에 모아두면 여러 가지 장점이 있어요:
- **재사용성**: 여러 컴포넌트에서 같은 API를 쉽게 사용
- **일관성**: 데이터 변환(snake_case → camelCase)을 한 곳에서 처리
- **테스트 용이성**: API 호출을 mock하기 쉬움

## 어떻게 작동하나요?

백엔드와 프론트엔드는 다른 명명 규칙을 써요:
- 백엔드 (Python): `task_number`, `code_language` (snake_case)
- 프론트엔드 (TypeScript): `taskNumber`, `codeLanguage` (camelCase)

서비스에서 이 변환을 자동으로 처리해요:

```typescript
// 백엔드에서 받은 데이터를 프론트엔드 형식으로 변환
const transformTask = (dto) => ({
  id: dto.id,
  taskNumber: dto.task_number,  // 변환!
  codeLanguage: dto.code_language,  // 변환!
  // ...
})
```

## TDD로 어떻게 테스트했나요?

- 11개의 테스트 케이스 작성
- axios를 mock해서 실제 API 호출 없이 테스트
- getTasks, getTask, createTask, updateTask, deleteTask, getTaskCode 등 테스트

## 관련 파일

- `frontend/src/services/task-service.ts` - 서비스 구현
- `frontend/src/services/task-service.test.ts` - 테스트 코드

## 배운 개념

- **DTO (Data Transfer Object)**: API 응답 데이터의 타입 정의
- **FormData**: 파일 업로드를 위한 multipart/form-data 요청
- **vi.mock**: Vitest에서 모듈 mock하기

## 주의사항

- 파일 업로드 시 `Content-Type: multipart/form-data` 헤더가 필요해요
- 타입 안전성을 위해 백엔드 응답 타입과 프론트엔드 타입을 분리했어요

## 다음 단계

T081에서 태스크 생성 모달을 구현할 예정이에요.
