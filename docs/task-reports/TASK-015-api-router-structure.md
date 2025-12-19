# Task 015: API 라우터 구조 설정

**작성일**: 2025-11-19
**작업 유형**: 백엔드 인프라 - API 버전 관리 및 라우팅
**관련 파일**:
- `backend/src/api/__init__.py` (생성)
- `backend/src/main.py` (수정)
- `backend/tests/unit/test_api_router.py` (생성)

---

## 무엇을 만들었나요?

API 엔드포인트를 체계적으로 관리하기 위한 라우터 구조를 만들었습니다. 모든 API 엔드포인트가 `/api/v1` 경로 아래에 조직화되도록 설정했습니다.

주요 기능:
1. **API 버전 관리**: `/api/v1` prefix로 모든 엔드포인트 그룹화
2. **라우터 분리**: 메인 앱과 API 엔드포인트 분리
3. **기본 엔드포인트**: `/api/v1/health`, `/api/v1/info` 추가
4. **확장 가능한 구조**: 향후 auth, projects, tasks 등 추가 용이

---

## 왜 이렇게 만들었나요?

### 1. API 버전 관리의 필요성

웹 서비스를 운영하다 보면 API를 변경해야 할 때가 있습니다. 예를 들어:
- 새로운 기능 추가
- 데이터 형식 변경
- 보안 강화

하지만 기존 사용자(앱, 웹사이트)는 여전히 옛날 방식을 사용하고 있을 수 있습니다. 이때 버전 관리가 필요합니다.

**실생활 비유**: 스마트폰 앱 업데이트
- iOS 15를 쓰는 사람도 있고, iOS 17을 쓰는 사람도 있습니다
- 앱은 두 버전 모두 지원해야 합니다
- API도 마찬가지로 `/api/v1`, `/api/v2`로 구분하여 여러 버전을 동시에 지원합니다

### 2. 경로 구조화의 이점

**구조화 전** (Bad):
```
POST /register
POST /login
GET /projects
POST /projects
GET /tasks
```
문제점: 모든 엔드포인트가 루트에 뒤섞여 있어 관리가 어렵습니다.

**구조화 후** (Good):
```
POST /api/v1/auth/register
POST /api/v1/auth/login
GET /api/v1/projects
POST /api/v1/projects
GET /api/v1/tasks
```
장점:
- 카테고리별로 그룹화 (`/auth`, `/projects`, `/tasks`)
- 버전 명시 (`/api/v1`)
- 체계적이고 예측 가능한 URL 구조

### 3. 라우터 분리의 이유

**음식점 비유**:
- **메인 앱** = 음식점 건물 (전체 인프라)
- **API 라우터** = 주방 (실제 요리하는 곳)

건물 관리(CORS, 미들웨어)와 주방 운영(API 엔드포인트)을 분리하면:
- 각자의 책임이 명확해집니다
- 주방(API)만 교체하거나 확장하기 쉽습니다
- 코드가 깔끔하고 유지보수가 쉽습니다

---

## 어떻게 작동하나요?

### 1. 라우터 생성 과정

```python
# backend/src/api/__init__.py

# 1. APIRouter 생성 (주방 설정)
api_router = APIRouter(
    prefix="/api/v1",  # 모든 경로에 이 prefix 자동 추가
    responses={...}     # 공통 에러 응답 정의
)

# 2. 엔드포인트 등록
@api_router.get("/health")
async def api_health_check():
    return {"status": "healthy", "api_version": "1.0"}

# 3. 실제 경로는 /api/v1/health가 됨
```

### 2. 메인 앱에 연결

```python
# backend/src/main.py

from src.api import api_router

app = FastAPI(...)

# API 라우터를 메인 앱에 포함
app.include_router(api_router)
```

### 3. 요청 처리 흐름

```
사용자 요청: GET /api/v1/health
    ↓
FastAPI 메인 앱 (CORS, 미들웨어 처리)
    ↓
API 라우터 확인 (/api/v1 prefix 매칭)
    ↓
health 엔드포인트 실행
    ↓
응답 반환: {"status": "healthy", ...}
```

### 4. 향후 라우터 추가 방법

```python
# 미래에 추가할 라우터들

# backend/src/api/auth.py
auth_router = APIRouter()

@auth_router.post("/register")
async def register():
    ...

# backend/src/api/__init__.py
from src.api.auth import auth_router

api_router.include_router(
    auth_router,
    prefix="/auth",  # /api/v1/auth/register
    tags=["Authentication"]
)
```

---

## TDD 사이클은 어떻게 진행했나요?

### 🔴 RED 단계

8개의 테스트 작성:
1. `api_router` 모듈을 import할 수 있는가?
2. 라우터에 prefix가 설정되어 있는가?
3. `/api/v1/health` 엔드포인트가 작동하는가?
4. `/api/v1/info` 엔드포인트가 작동하는가?
5. 기존 `/` 엔드포인트는 여전히 작동하는가?
6. 기존 `/health` 엔드포인트는 여전히 작동하는가?
7. 메인 앱에 API 라우터가 포함되어 있는가?
8. 라우터가 태그를 지원하는가?

**결과**: 6개 실패, 2개 통과 (기존 엔드포인트만 통과) ✅

**커밋**: `test: Task 015 - API router structure - RED`

### 🟢 GREEN 단계

구현 내용:

**1. API 라우터 생성** (`backend/src/api/__init__.py`):
- `/api/v1` prefix 설정
- `/health` 엔드포인트 (API 버전 정보 포함)
- `/info` 엔드포인트 (사용 가능한 엔드포인트 목록)
- 향후 확장을 위한 주석 가이드

**2. 메인 앱에 연결** (`backend/src/main.py`):
- `api_router` import
- `app.include_router(api_router)` 추가

**결과**: 8개 테스트 모두 통과 ✅

**커밋**: `feat: Task 015 - API router structure - GREEN`

### 🔵 REFACTOR 단계

코드 품질 확인:
- ✅ Ruff 린터: All checks passed!
- ✅ 100% 코드 커버리지 (api/__init__.py, main.py)
- ✅ 명확한 docstring과 타입 힌트
- ✅ 적절한 구조와 조직화

추가 리팩토링이 필요 없어서 이 단계는 생략했습니다.

---

## 핵심 개념

### 1. API 라우터 (APIRouter)

FastAPI에서 제공하는 라우팅 조직화 도구입니다.

**특징**:
- 엔드포인트를 그룹으로 묶음
- 공통 prefix 설정
- 태그로 문서화 그룹화
- 재사용 가능한 모듈

### 2. 경로 Prefix

모든 엔드포인트에 자동으로 추가되는 경로 접두사입니다.

**예시**:
```python
router = APIRouter(prefix="/api/v1")

@router.get("/users")  # 실제 경로: /api/v1/users
@router.get("/tasks")  # 실제 경로: /api/v1/tasks
```

### 3. 라우터 중첩 (Router Nesting)

라우터 안에 다른 라우터를 포함시킬 수 있습니다.

```python
# 메인 API 라우터
api_router = APIRouter(prefix="/api/v1")

# 인증 라우터
auth_router = APIRouter()
@auth_router.post("/login")
...

# 중첩
api_router.include_router(auth_router, prefix="/auth")
# 최종 경로: /api/v1/auth/login
```

### 4. 버전 관리 전략

**URL 경로 버전 관리** (현재 사용):
```
/api/v1/users
/api/v2/users
```
장점: 명확하고 직관적, 문서화 쉬움

**헤더 버전 관리** (대안):
```
GET /users
Header: API-Version: 1.0
```
장점: URL이 깔끔함

---

## 주의사항

### 1. 라우터 순서

라우터를 포함하는 순서가 중요합니다:

```python
# ❌ 잘못된 예
app.include_router(catch_all_router)  # 모든 요청을 잡음
app.include_router(api_router)        # 여기 도달 못함

# ✅ 올바른 예
app.include_router(api_router)        # 특정 경로 먼저
app.include_router(catch_all_router)  # 나머지 잡기
```

### 2. Prefix 중복

Prefix가 중복되지 않도록 주의:

```python
# ❌ 중복
api_router = APIRouter(prefix="/api/v1")
app.include_router(api_router, prefix="/api/v1")
# 결과: /api/v1/api/v1/health (잘못됨!)

# ✅ 올바름
api_router = APIRouter(prefix="/api/v1")
app.include_router(api_router)
# 결과: /api/v1/health
```

### 3. 기존 엔드포인트 유지

루트 레벨 엔드포인트(`/`, `/health`)는 유지했습니다:
- 로드 밸런서나 모니터링 도구가 사용할 수 있습니다
- API 버전과 무관한 일반 정보 제공

---

## 다음 단계

이제 API 라우터 구조가 완성되었으므로, 각 기능별 라우터를 추가할 준비가 되었습니다:

### T016-T022: 나머지 인프라
- **T016**: 에러 처리 미들웨어 및 예외 스키마
- **T017**: Celery 앱과 Redis 연결
- **T018-T022**: 프론트엔드 기반 설정

### 향후 API 라우터 추가 (Phase 3 이후)
- **T028-T031**: `/api/v1/auth` - 인증 엔드포인트
- **T046-T050**: `/api/v1/projects` - 프로젝트 CRUD
- **T070-T075**: `/api/v1/tasks` - 태스크 관리
- **T097-T098**: `/api/v1/documents` - 학습 문서
- **T120-T121**: `/api/v1/practice` - 연습 문제
- **T136-T138**: `/api/v1/qa` - Q&A 시스템
- **T154-T155**: `/api/v1/progress` - 진도 추적
- **T173-T177**: `/api/v1/trash` - 휴지통 관리

각 라우터는 `backend/src/api/` 디렉토리에 별도 파일로 생성되고, `api_router.include_router()`로 연결됩니다.

---

## 수정된 파일

### 생성된 파일
- `backend/src/api/__init__.py` - API 라우터 메인 모듈
- `backend/tests/unit/test_api_router.py` - 유닛 테스트 (8개)

### 수정된 파일
- `backend/src/main.py` - API 라우터 포함

### 커밋 히스토리
1. `test: Task 015 - API router structure - RED`
2. `feat: Task 015 - API router structure - GREEN`

---

## 참고 자료

- FastAPI APIRouter: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- API Versioning Best Practices: https://restfulapi.net/versioning/
- Routing in FastAPI: https://fastapi.tiangolo.com/tutorial/path-params/

---

**테스트 결과**: ✅ 8개 테스트 모두 통과
**코드 커버리지**: 100% (api/__init__.py, main.py)
**Ruff 린터**: ✅ 모든 검사 통과
