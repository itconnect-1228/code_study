# Task Report: T046-T050 Project API Endpoints

## 개요

| 항목 | 내용 |
|------|------|
| Task ID | T046, T047, T048, T049, T050 |
| 제목 | Project API Endpoints |
| 상태 | 완료 |
| 개발 방법 | TDD (RED-GREEN-REFACTOR) |

## 구현된 기능

### T046: GET /projects - 프로젝트 목록 조회
- 현재 사용자의 모든 프로젝트 조회
- `include_trashed` 쿼리 파라미터로 휴지통 프로젝트 포함 여부 선택
- 인증 필수 (401 Unauthorized)

### T047: POST /projects - 프로젝트 생성
- 제목(필수)과 설명(선택)으로 새 프로젝트 생성
- 201 Created 응답 반환
- 인증 필수

### T048: GET /projects/{project_id} - 프로젝트 상세 조회
- UUID로 특정 프로젝트 조회
- 소유권 검증 (403 Forbidden)
- 존재하지 않는 프로젝트 (404 Not Found)

### T049: PATCH /projects/{project_id} - 프로젝트 수정
- 제목 또는 설명 부분 수정
- 소유권 검증 필수
- 수정된 프로젝트 반환

### T050: DELETE /projects/{project_id} - 프로젝트 삭제 (소프트 삭제)
- 30일 후 영구 삭제 예정으로 휴지통 이동
- 204 No Content 응답
- 소유권 검증 필수

## 파일 변경 내역

### 신규 파일
| 파일 | 설명 |
|------|------|
| `backend/src/api/projects.py` | 프로젝트 API 라우터 (5개 엔드포인트) |
| `backend/tests/unit/api/test_projects.py` | 프로젝트 API 단위 테스트 (22개 테스트) |

### 수정된 파일
| 파일 | 변경 내용 |
|------|-----------|
| `backend/src/api/schemas.py` | CreateProjectRequest, UpdateProjectRequest, ProjectResponse, ProjectListResponse 스키마 추가 |
| `backend/src/api/router.py` | projects 라우터 등록 (`/projects` prefix) |

## API 스키마

### CreateProjectRequest
```python
class CreateProjectRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
```

### UpdateProjectRequest
```python
class UpdateProjectRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
```

### ProjectResponse
```python
class ProjectResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    created_at: str
    updated_at: str
    last_activity_at: str
    deletion_status: str
    trashed_at: str | None
```

### ProjectListResponse
```python
class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int
```

## 테스트 결과

```
22 passed in 2.5s
```

### 테스트 커버리지

| 테스트 클래스 | 테스트 수 | 설명 |
|--------------|----------|------|
| TestGetProjects | 3 | 목록 조회, 인증 실패, include_trashed |
| TestCreateProject | 4 | 생성 성공, 인증 실패, 제목 누락, 제목 유효성 |
| TestGetProject | 4 | 조회 성공, 인증 실패, 404 Not Found, 소유권 |
| TestUpdateProject | 6 | 전체 수정, 부분 수정, 인증 실패, 404, 소유권, 빈 요청 |
| TestDeleteProject | 5 | 삭제 성공, 인증 실패, 404, 소유권, 소프트 삭제 검증 |

## 의존성

- FastAPI
- SQLAlchemy (AsyncSession)
- Pydantic
- ProjectService (서비스 계층)
- get_current_user (인증 의존성)

## 에러 처리

| HTTP 상태 코드 | 에러 코드 | 설명 |
|---------------|----------|------|
| 401 | UNAUTHORIZED | 인증 토큰 없음 또는 유효하지 않음 |
| 403 | ACCESS_DENIED | 프로젝트 소유권 없음 |
| 404 | PROJECT_NOT_FOUND | 프로젝트가 존재하지 않음 |
| 422 | VALIDATION_ERROR | 요청 데이터 유효성 검사 실패 |
