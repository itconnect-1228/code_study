# Task 016: 에러 처리 미들웨어 및 예외 스키마 구현

**완료일**: 2025-12-20
**관련 파일**: backend/src/api/exceptions.py, backend/src/main.py, backend/tests/unit/test_exceptions.py

## 무엇을 만들었나요?

API 서버에서 발생하는 모든 에러를 일관된 형식으로 처리하는 시스템을 구축했습니다. 이는 마치 **응급실의 트리아지 시스템**과 같아서, 다양한 유형의 문제들을 체계적으로 분류하고 적절하게 대응하는 역할을 합니다.

웹 애플리케이션에서는 수많은 종류의 오류가 발생할 수 있습니다:
- 사용자가 잘못된 정보를 입력하는 경우 (400 Bad Request)
- 로그인이 필요한데 로그인하지 않은 경우 (401 Unauthorized)
- 권한이 없는 리소스에 접근하려는 경우 (403 Forbidden)
- 존재하지 않는 데이터를 요청하는 경우 (404 Not Found)
- 중복된 데이터를 생성하려는 경우 (409 Conflict)
- 유효성 검사가 실패한 경우 (422 Validation Error)

이 작업을 통해 이런 모든 에러들이 **같은 형식**으로 사용자에게 전달되도록 만들었습니다.

## 왜 이렇게 만들었나요?

### 1. 일관성 있는 에러 응답
프론트엔드 개발자와 API 사용자들이 에러를 처리하기 쉽도록, 모든 에러가 같은 구조를 따르도록 했습니다:

```json
{
  "error": "사용자에게 보여줄 메시지",
  "code": "기계가 읽을 수 있는 에러 코드",
  "detail": "추가적인 상세 정보 (선택)"
}
```

### 2. HTTP 상태 코드의 정확한 사용
각 에러 유형에 맞는 HTTP 상태 코드를 자동으로 사용합니다:
- `BadRequestException` → 400
- `AuthenticationException` → 401
- `AuthorizationException` → 403
- `NotFoundException` → 404
- `ConflictException` → 409
- `ValidationException` → 422

### 3. 보안 고려
서버 내부의 민감한 정보가 사용자에게 노출되지 않도록, 예상치 못한 에러는 "Internal server error"라는 일반적인 메시지로 변환됩니다.

## 어떻게 작동하나요?

```python
# 인증 실패 시
raise AuthenticationException(message="로그인이 필요합니다")

# 리소스를 찾을 수 없을 때
raise NotFoundException(message="프로젝트를 찾을 수 없습니다")

# 유효성 검사 실패 시
raise ValidationException(
    message="입력 데이터가 유효하지 않습니다",
    errors=[{"field": "email", "error": "올바른 이메일 형식이 아닙니다"}]
)
```

예외 핸들러가 `add_exception_handlers(app)`으로 자동 등록되어, 어디서든 예외가 발생하면 적절한 JSON 응답으로 변환됩니다.

## 테스트는 어떻게 했나요?

### 🔴 RED 단계
29개의 테스트 케이스를 먼저 작성:
- 각 예외 클래스의 속성 검증 (18개 테스트)
- 에러 응답 포맷팅 함수 검증 (4개 테스트)
- 예외 핸들러 통합 테스트 (5개 테스트)
- add_exception_handlers 함수 테스트 (2개 테스트)

### 🟢 GREEN 단계
`backend/src/api/exceptions.py` 파일을 생성:
1. `AppException` 기본 클래스
2. 6개의 특화된 예외 클래스
3. `format_error_response()` 함수
4. 예외 핸들러 함수들
5. `add_exception_handlers()` 등록 함수

### 🔵 REFACTOR 단계
`backend/src/main.py`에 예외 핸들러를 자동 등록하도록 통합. 전체 115개 단위 테스트 통과!

## 수정된 파일

### 생성된 파일
- `backend/src/api/exceptions.py` - 예외 클래스 및 핸들러
- `backend/tests/unit/test_exceptions.py` - 29개 테스트 케이스

### 수정된 파일
- `backend/src/main.py` - 예외 핸들러 등록 추가

## 관련 개념

1. **예외 처리 (Exception Handling)**: 프로그램 실행 중 발생하는 오류를 감지하고 적절히 대응하는 메커니즘
2. **HTTP 상태 코드**: 서버의 응답 상태를 나타내는 3자리 숫자 코드
3. **미들웨어**: 요청과 응답 사이에서 공통 기능을 처리하는 계층

## 주의사항

- 새로운 API 엔드포인트를 만들 때는 적절한 예외 클래스를 사용하세요
- 사용자에게 민감한 정보(데이터베이스 구조, 내부 경로 등)가 노출되지 않도록 주의하세요
- 유효성 검사 오류는 `ValidationException`을 사용하고 `errors` 리스트를 포함시키세요

## 다음 단계

이제 에러 처리 인프라가 완성되었으므로:
1. **T017**: Celery 앱과 Redis 연결 설정
2. **T018-T022**: 프론트엔드 기반 설정

---

**TDD 사이클**: ✅ RED → GREEN → REFACTOR
