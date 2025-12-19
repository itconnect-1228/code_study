# Task 015: API 라우터 구조 생성

**완료일**: 2025-12-19
**관련 파일**:
- `backend/src/api/__init__.py` (생성)
- `backend/src/api/router.py` (생성)
- `backend/src/main.py` (수정)

---

## 무엇을 만들었나요?

API 라우터 구조를 만들었습니다. 모든 API 엔드포인트가 `/api/v1` 경로 아래에서 체계적으로 관리됩니다.

**생성된 파일 구조:**
```
backend/src/api/
├── __init__.py    # api_router를 export
└── router.py      # API 라우터 메인 모듈
```

**추가된 엔드포인트:**
- `GET /api/v1/health` - API 상태 확인
- `GET /api/v1/info` - 사용 가능한 API 엔드포인트 목록

---

## 왜 이렇게 만들었나요?

### 1. API 버전 관리의 필요성

웹 서비스를 운영하다 보면 API를 변경해야 할 때가 있습니다. 하지만 기존 사용자는 여전히 옛날 방식을 사용하고 있을 수 있습니다.

**실생활 비유**: 스마트폰 앱 업데이트
- iOS 15를 쓰는 사람도 있고, iOS 17을 쓰는 사람도 있습니다
- 앱은 두 버전 모두 지원해야 합니다
- API도 `/api/v1`, `/api/v2`로 구분하여 여러 버전을 동시에 지원합니다

### 2. 파일 분리 (router.py)

라우터 로직을 별도 파일로 분리하면:
- 코드가 깔끔하고 유지보수가 쉽습니다
- 향후 다른 라우터(auth, projects 등)를 추가하기 쉽습니다
- 테스트하기 편합니다

---

## 어떻게 작동하나요?

### 요청 처리 흐름

```
사용자 요청: GET /api/v1/health
    ↓
FastAPI 메인 앱 (main.py)
    ↓
API 라우터 확인 (/api/v1 prefix 매칭)
    ↓
router.py의 api_health_check() 실행
    ↓
응답 반환: {"status": "healthy", "api_version": "v1", ...}
```

### 코드 구조

```python
# router.py
api_router = APIRouter(prefix="/api/v1")

@api_router.get("/health")
async def api_health_check():
    return {"status": "healthy", "api_version": "v1", ...}

@api_router.get("/info")
async def api_info():
    return {"api_version": "v1", "endpoints": {...}, ...}
```

```python
# main.py
from .api import api_router
app.include_router(api_router)
```

---

## 테스트 결과

모든 엔드포인트 정상 작동 확인:

| 엔드포인트 | 상태 | 설명 |
|-----------|------|------|
| `GET /` | ✅ OK | Task 14 - 루트 엔드포인트 |
| `GET /health` | ✅ OK | Task 14 - 헬스 체크 |
| `GET /api/v1/health` | ✅ OK | Task 15 - API v1 헬스 체크 |
| `GET /api/v1/info` | ✅ OK | Task 15 - API 정보 |

---

## 핵심 개념

### API 라우터 (APIRouter)

FastAPI에서 제공하는 라우팅 조직화 도구입니다.

**특징**:
- 엔드포인트를 그룹으로 묶음
- 공통 prefix 설정
- 재사용 가능한 모듈

### Prefix (접두사)

모든 엔드포인트에 자동으로 추가되는 경로 접두사입니다.

```python
router = APIRouter(prefix="/api/v1")

@router.get("/health")  # 실제 경로: /api/v1/health
@router.get("/info")    # 실제 경로: /api/v1/info
```

---

## 주의사항

1. **Prefix 중복 주의**: `include_router()`에 prefix를 다시 지정하면 중복됩니다
2. **라우터 순서**: 특정 경로 라우터를 먼저, catch-all 라우터를 나중에 등록
3. **기존 엔드포인트 유지**: `/`와 `/health`는 Task 14에서 만든 것으로 유지됨

---

## 다음 단계

이 라우터 구조 위에 각 기능별 라우터가 추가됩니다:

- **T028-T031**: `/api/v1/auth` - 인증 엔드포인트
- **T046-T050**: `/api/v1/projects` - 프로젝트 CRUD
- **T070-T075**: `/api/v1/tasks` - 태스크 관리
- **T097-T098**: `/api/v1/documents` - 학습 문서

---

## 수정된 파일

| 파일 | 변경 내용 |
|------|-----------|
| `backend/src/api/__init__.py` | 생성 - api_router export |
| `backend/src/api/router.py` | 생성 - API 라우터 정의, /health, /info 엔드포인트 |
| `backend/src/main.py` | 수정 - api_router import 및 include_router 호출 |
