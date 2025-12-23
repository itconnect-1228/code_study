# Task 026: TokenService 구현

**완료 일자**: 2025-12-23
**작업 유형**: Backend Service Layer (JWT Token Management)
**작업 방식**: TDD (RED-GREEN-REFACTOR)

---

## 무엇을 만들었나요?

JWT **액세스 토큰과 리프레시 토큰**을 생성, 검증, 순환하는 서비스를 구현했습니다.

### TokenService란?

웹사이트의 "보안 열쇠 관리 부서"와 같은 역할을 합니다:
- **액세스 토큰 발급**: 15분 유효한 짧은 열쇠
- **리프레시 토큰 발급**: 7일 유효한 긴 열쇠
- **토큰 검증**: 위조되지 않았는지 확인
- **토큰 순환**: 오래된 열쇠를 폐기하고 새 열쇠 발급

**비유**: 호텔 키카드 시스템처럼, 체크인 시 카드를 발급하고, 유효기간을 확인하며, 필요 시 재발급하거나 무효화합니다.

---

## 왜 이렇게 만들었나요?

### 1. 이중 토큰 전략 (Dual Token Strategy)

**액세스 토큰 (짧음, 15분)**:
- API 요청마다 사용
- 짧은 유효기간으로 보안 강화
- 데이터베이스 조회 불필요 (stateless)

**리프레시 토큰 (길음, 7일)**:
- 액세스 토큰 갱신용
- 데이터베이스에 저장하여 폐기 가능
- 사용 시마다 새로 발급 (rotation)

**비유**:
- 액세스 토큰 = 일일 출입증 (매일 아침 재발급)
- 리프레시 토큰 = 사원증 (장기 사용, 퇴사 시 회수)

### 2. JWT (JSON Web Token) 사용

```python
payload = {
    "sub": str(user_id),  # 사용자 ID
    "exp": expire,         # 만료 시간
    "iat": now,            # 발급 시간
    "type": "access",      # 토큰 유형
    "jti": str(uuid4()),   # 고유 식별자 (리프레시 토큰만)
}
```

**JWT의 장점**:
- **Self-contained**: 토큰 안에 모든 정보 포함
- **Stateless**: 서버가 세션 저장 불필요
- **Portable**: 여러 서버 간 공유 가능

### 3. 리프레시 토큰 해시 저장

```python
token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
```

**왜 원본이 아닌 해시를 저장하나요?**
- 데이터베이스가 해킹당해도 실제 토큰 값을 알 수 없음
- 비밀번호를 해시로 저장하는 것과 같은 원리

**비유**: 은행 금고 열쇠를 직접 보관하지 않고, 열쇠의 지문만 기록하는 것과 같습니다.

### 4. JTI (JWT ID)로 고유성 보장

```python
"jti": str(uuid4()),  # Unique token identifier
```

**문제**: 같은 초에 두 개의 리프레시 토큰을 생성하면 동일한 토큰이 생성될 수 있음
**해결**: JTI를 추가하여 각 토큰이 고유한 UUID를 가지도록 함

---

## 어떻게 작동하나요?

### 핵심 메서드

#### 1. create_access_token() - 액세스 토큰 생성

```python
async def create_access_token(user_id: UUID, expires_delta: timedelta | None = None) -> str:
    # 1. 만료 시간 계산 (기본 15분)
    # 2. JWT payload 구성
    # 3. JWT 인코딩 및 반환
```

**특징**:
- 데이터베이스에 저장하지 않음 (stateless)
- 짧은 유효기간으로 보안 강화
- API 요청마다 사용

#### 2. create_refresh_token() - 리프레시 토큰 생성

```python
async def create_refresh_token(user_id: UUID, expires_delta: timedelta | None = None) -> str:
    # 1. 만료 시간 계산 (기본 7일)
    # 2. JWT payload 구성 (JTI 포함)
    # 3. JWT 인코딩
    # 4. 해시값을 데이터베이스에 저장
    # 5. 원본 토큰 반환
```

**특징**:
- SHA-256 해시로 저장 (보안)
- JTI로 고유성 보장
- 데이터베이스에 저장하여 폐기 가능

#### 3. verify_access_token() - 액세스 토큰 검증

JWT 서명과 만료 시간만 확인 (데이터베이스 조회 없음)

#### 4. verify_refresh_token() - 리프레시 토큰 검증

JWT 검증 + 데이터베이스에서 폐기 여부 확인

#### 5. rotate_refresh_token() - 토큰 순환

이전 토큰 폐기 후 새 토큰 발급 (보안 강화)

#### 6. revoke_all_user_tokens() - 모든 토큰 폐기

"모든 장치에서 로그아웃" 기능

#### 7. cleanup_expired_tokens() - 만료된 토큰 정리

배경 작업으로 주기적 실행하여 데이터베이스 공간 확보

---

## TDD 사이클

### 🔴 RED Phase
- **작성한 테스트**: 27개 테스트 케이스 작성
  - 액세스 토큰 생성/검증 (3개)
  - 리프레시 토큰 생성/검증 (7개)
  - 토큰 순환 (4개)
  - 토큰 폐기 (5개)
  - 만료된 토큰 정리 (2개)
  - 사용자 ID 추출 (3개)
- **테스트 결과**: ❌ 실패 (모듈 없음)
- **커밋**: `2b2723e - test: T026 TokenService - RED`

### 🟢 GREEN Phase
- **구현 내용**: TokenService 클래스 구현
  - JWT 생성/검증 로직
  - SHA-256 해시로 리프레시 토큰 저장
  - JTI로 토큰 고유성 보장
  - 토큰 순환 및 폐기 기능
- **테스트 결과**: ✅ 27개 모두 통과
- **커밋**: `00fa00c - feat: T026 TokenService - GREEN`

### 🔵 REFACTOR Phase
- **개선 내용**:
  - auth 패키지 __init__.py에 TokenService export 추가
  - verify_refresh_token 메서드 간소화 (is_valid 속성 활용)
  - 코드 가독성 향상
- **테스트 결과**: ✅ 여전히 27개 모두 통과
- **커밋**: `abc36e6 - refactor: T026 TokenService - REFACTOR`

---

## 수정된 파일

| 파일 | 설명 |
|------|------|
| `backend/src/services/auth/token_service.py` | TokenService 클래스 구현 (305줄) |
| `backend/src/services/auth/__init__.py` | TokenService export 추가 |
| `backend/tests/unit/test_token_service.py` | 27개 테스트 케이스 (486줄) |

---

## 관련 개념

### 1. JWT (JSON Web Token)

**구조**: Header.Payload.Signature

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.    # Header
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6...  # Payload
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c  # Signature
```

**비유**: 봉인된 편지처럼, 누군가 내용을 변경하면 봉인(서명)이 깨져서 알 수 있습니다.

### 2. Token Rotation (토큰 순환)

매번 사용 시 **새 토큰을 발급하고 이전 토큰을 폐기**:

```
첫 로그인: 토큰 A 발급
토큰 갱신 1: 토큰 A 폐기 → 토큰 B 발급
토큰 갱신 2: 토큰 B 폐기 → 토큰 C 발급
```

**보안 이점**: 토큰이 탈취되어도 한 번만 사용 가능

### 3. SHA-256 해시

데이터를 256비트 고정 길이 해시로 변환:
- 일방향 (해시에서 원본 복원 불가)
- 같은 입력 → 같은 출력
- 조금만 변경해도 완전히 다른 해시

---

## 주의사항

### 보안 고려사항

1. **JWT_SECRET_KEY는 반드시 변경**
   ```bash
   # openssl rand -hex 32 로 생성
   ```

2. **액세스 토큰은 저장하지 않음**
   - 클라이언트에서 HTTPOnly 쿠키나 메모리에 보관

3. **리프레시 토큰 원본은 절대 로그에 남기지 않음**

### 환경 변수 설정

```bash
JWT_SECRET_KEY=<openssl rand -hex 32로 생성한 값>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## 다음 단계

1. **T027: Authentication Dependency** - 라우트 보호를 위한 미들웨어
2. **T028-031: Auth API 엔드포인트** - /auth/register, /auth/login, /auth/logout, /auth/refresh

TokenService는 완성되었고, 다음 단계에서 API 엔드포인트에서 이 서비스를 사용하여 실제 인증 플로우를 구현할 예정입니다.
