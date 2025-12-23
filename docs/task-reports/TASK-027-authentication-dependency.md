# Task 027: Authentication Dependency (인증 의존성)

**완료일**: 2025-12-23
**관련 파일**:
- `backend/src/api/dependencies.py` (생성)
- `backend/tests/unit/test_dependencies.py` (생성)

## 무엇을 만들었나요?

FastAPI 라우트(API 엔드포인트)를 보호하기 위한 **인증 의존성(Authentication Dependency)**을 만들었습니다.

쉽게 설명하면, 웹사이트에서 "로그인한 사용자만 볼 수 있는 페이지"를 만들 때 필요한 **문지기 역할**을 하는 코드입니다. 마치 VIP 라운지에 들어가기 전에 회원증을 확인하는 직원처럼, 이 코드가 사용자의 "인증 토큰"을 확인하고 통과 여부를 결정합니다.

두 가지 버전을 만들었습니다:
1. **get_current_user**: 반드시 로그인해야 접근 가능 (없으면 401 에러)
2. **get_current_user_optional**: 로그인 안 해도 접근 가능 (로그인 시 사용자 정보 제공)

## 왜 이렇게 만들었나요?

**쿠키 기반 인증을 선택한 이유:**
- HTTPOnly 쿠키는 JavaScript로 접근 불가능해서 XSS 공격으로부터 안전합니다
- 브라우저가 자동으로 쿠키를 전송하므로 프론트엔드 코드가 단순해집니다
- API 명세(api-spec.yaml)에서 `cookieAuth`를 사용하도록 정의했기 때문입니다

**의존성 주입 패턴을 사용한 이유:**
- FastAPI의 `Depends()` 시스템을 활용하면 코드 중복을 줄일 수 있습니다
- 테스트할 때 쉽게 모킹(mocking)할 수 있습니다
- 각 라우트에서 인증 로직을 반복하지 않아도 됩니다

## 어떻게 작동하나요?

```python
# 1. 쿠키에서 access_token 추출
access_token = request.cookies.get("access_token")

# 2. JWT 토큰 검증 및 디코딩
payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])

# 3. 토큰 타입 확인 (access 토큰만 허용, refresh 토큰 거부)
if payload.get("type") != "access":
    raise AuthenticationException(...)

# 4. 토큰에서 user_id 추출 후 DB에서 사용자 조회
user = await db.execute(select(User).where(User.id == user_id))
```

**사용 예시:**
```python
@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_user)
):
    return {"user_email": current_user.email}
```

## TDD 사이클

### 🔴 RED Phase
- 작성한 테스트: 9개의 테스트 케이스 (유효한 토큰, 누락된 토큰, 잘못된 토큰, 만료된 토큰, 존재하지 않는 사용자, refresh 토큰 거부, optional 버전 3가지)
- 테스트 결과: ❌ 실패 (ModuleNotFoundError - dependencies.py가 없음)
- **커밋**: `cdb0594 - test: T027 AuthenticationDependency - RED`

### 🟢 GREEN Phase
- 구현 내용: `get_current_user`와 `get_current_user_optional` 함수 구현
- 테스트 결과: ✅ 9개 테스트 모두 통과
- **커밋**: `afd1a5f - feat: T027 AuthenticationDependency - GREEN`

### 🔵 REFACTOR Phase
- 개선 내용:
  - `ACCESS_TOKEN_COOKIE` 상수 추가 (매직 스트링 제거)
  - `_decode_access_token` 헬퍼 함수 분리 (관심사 분리)
  - 상세한 docstring 및 사용 예시 추가
- 테스트 결과: ✅ 여전히 9개 테스트 통과
- **커밋**: `d859b31 - refactor: T027 AuthenticationDependency - REFACTOR`

## 수정된 파일

| 파일 | 변경 내용 |
|------|----------|
| `backend/src/api/dependencies.py` | 새 파일 - 인증 의존성 함수들 (165줄) |
| `backend/tests/unit/test_dependencies.py` | 새 파일 - 9개 테스트 케이스 |

## 관련 개념

- **JWT (JSON Web Token)**: 사용자 정보를 담은 암호화된 토큰. 마치 암호화된 신분증 같습니다.
- **FastAPI Dependency Injection**: 함수가 필요한 것들을 자동으로 제공받는 패턴. 레스토랑에서 주문만 하면 재료, 요리, 서빙이 알아서 되는 것과 비슷합니다.
- **HTTPOnly Cookie**: JavaScript로 읽을 수 없는 특별한 쿠키. 해커가 스크립트로 쿠키를 훔칠 수 없습니다.

## 주의사항

1. **토큰 타입 검증**: access_token만 허용합니다. refresh_token을 사용하면 401 에러가 발생합니다.
2. **사용자 존재 확인**: 토큰이 유효해도 DB에 사용자가 없으면 401 에러가 발생합니다.
3. **쿠키 이름**: `access_token` 쿠키 이름은 프론트엔드와 일치해야 합니다.

## 다음 단계

다음 작업은 T028-T031로, 실제 인증 API 엔드포인트 구현입니다:
- T028: POST /auth/register (회원가입)
- T029: POST /auth/login (로그인)
- T030: POST /auth/logout (로그아웃)
- T031: POST /auth/refresh (토큰 갱신)

이 의존성들은 모든 보호된 API 엔드포인트에서 사용될 예정입니다.
