# Task 025: UserService 구현

**완료일**: 2025-12-23
**관련 파일**: backend/src/services/auth/user_service.py, backend/tests/unit/test_user_service.py

## 무엇을 만들었나요?

사용자 **회원가입, 로그인, 사용자 조회** 기능을 처리하는 서비스 레이어를 만들었습니다.

### UserService란?

웹사이트의 "회원 관리 부서"와 같은 역할을 합니다:
- **회원가입 창구**: 새로운 사용자 등록 처리
- **로그인 창구**: 비밀번호 확인 및 로그인 처리
- **회원 정보 조회**: 이메일 또는 ID로 사용자 찾기

**비유**: 은행 창구 직원처럼, 데이터베이스(금고)와 API 엔드포인트(고객) 사이에서 업무를 처리합니다.

## 왜 이렇게 만들었나요?

### 1. 서비스 레이어 패턴

**모델(Model) → 서비스(Service) → API 엔드포인트** 구조를 사용합니다.

- **Model (User)**: 데이터베이스 테이블 정의 (Task 023에서 완료)
- **Service (UserService)**: 비즈니스 로직 처리 (이번 작업)
- **API (auth.py)**: HTTP 요청 처리 (다음 작업)

**비유**:
- Model = 서류 양식
- Service = 업무 처리 규칙
- API = 고객 상담 창구

### 2. 보안 중심 설계

#### 비밀번호는 절대 원본 저장하지 않음
```python
password_hash = hash_password(password)  # Bcrypt 해싱
```

**비유**: 은행 비밀번호를 암호화된 형태로만 저장하는 것과 같습니다.

#### 에러 메시지에 힌트 주지 않기
```python
raise ValueError("Invalid email or password")  # 어느 것이 틀렸는지 알려주지 않음
```

**비유**: ATM에서 "카드번호 또는 비밀번호가 잘못되었습니다"라고만 표시하는 것과 같습니다.

### 3. Race Condition 처리

두 명이 동시에 같은 이메일로 가입하려 할 때:

```python
try:
    self.db.add(user)
    await self.db.commit()
except IntegrityError:
    await self.db.rollback()
    raise ValueError("Email already registered")
```

**비유**: 두 사람이 동시에 마지막 남은 좌석을 예약하려 할 때, 한 명만 성공하고 나머지는 "이미 예약됨" 메시지를 받는 것과 같습니다.

## 어떻게 작동하나요?

### 핵심 메서드

#### 1. register() - 회원가입
```python
async def register(email: str, password: str, skill_level: str = "Complete Beginner") -> User:
    # 1. 이메일 형식 검증
    # 2. 비밀번호 길이 검증 (최소 8자)
    # 3. 중복 이메일 확인
    # 4. 비밀번호 해싱
    # 5. 데이터베이스에 저장
```

#### 2. login() - 로그인
```python
async def login(email: str, password: str) -> User:
    # 1. 이메일로 사용자 찾기
    # 2. 비밀번호 확인 (constant-time 비교)
    # 3. 마지막 로그인 시간 업데이트
```

#### 3. get_user_by_email() / get_user_by_id() - 사용자 조회
```python
async def get_user_by_email(email: str) -> User | None:
    # 이메일로 데이터베이스 검색
    # 있으면 User 객체, 없으면 None 반환
```

## TDD 사이클

### 🔴 RED Phase
- 작성한 테스트: 14개 테스트 케이스 (회원가입 5개, 로그인 4개, 조회 5개)
- 테스트 결과: ❌ 실패 (예상대로)
- **커밋**: `f53ca1d - test: T025 UserService - RED`

### 🟢 GREEN Phase
- 구현 내용: UserService 클래스 전체 구현 (register, login, get_user_by_email, get_user_by_id)
- 테스트 결과: ✅ 14개 모두 통과
- **커밋**: `fcb1ddc - feat: T025 UserService - GREEN`

### 🔵 REFACTOR Phase
- 개선 내용:
  - MIN_PASSWORD_LENGTH, DEFAULT_SKILL_LEVEL 상수 추출
  - 보안 관련 문서화 (Security Note 섹션) 추가
  - 모든 메서드에 사용 예제 추가
  - 아키텍처 노트 추가
- 테스트 결과: ✅ 여전히 14개 모두 통과
- **커밋**: `e7cc2cc - refactor: T025 UserService - REFACTOR`

## 수정된 파일

| 파일 | 설명 |
|------|------|
| `backend/src/services/__init__.py` | 서비스 패키지 초기화 |
| `backend/src/services/auth/__init__.py` | 인증 서비스 패키지 (UserService 내보내기) |
| `backend/src/services/auth/user_service.py` | UserService 구현 (242줄) |
| `backend/tests/unit/test_user_service.py` | 14개 테스트 케이스 |

## 관련 개념

### 1. Service Layer Pattern
**3계층 아키텍처**:
```
API Layer (Controller) ← HTTP 요청/응답
    ↓
Service Layer (Business Logic) ← 이번 작업
    ↓
Data Layer (Model) ← 데이터베이스 접근
```

### 2. Async/Await
```python
async def register(...) -> User:
    await self.db.commit()  # 데이터베이스 작업 대기
```
**비유**: 식당에서 주문을 받은 직원이 요리가 나올 때까지 다른 손님을 응대하는 것과 같습니다.

### 3. Type Hints
```python
async def get_user_by_email(self, email: str) -> User | None:
```
- `email: str`: email 파라미터는 문자열 타입
- `-> User | None`: User 객체 또는 None을 반환

## 주의사항

### 보안 고려사항
1. **비밀번호 평문 저장 금지** - 항상 bcrypt 해시 사용
2. **에러 메시지에 힌트 주지 않기** - "Invalid email or password"만 사용
3. **이메일 검증** - User 모델과 동일한 regex 패턴 사용

### 데이터베이스 트랜잭션
```python
try:
    await self.db.commit()  # 성공 시 저장
except IntegrityError:
    await self.db.rollback()  # 실패 시 롤백
```
**중요**: 예외 발생 시 반드시 rollback()을 호출해야 합니다.

## 다음 단계

Task 025 완료 후 다음 작업:
1. **T026: TokenService 구현** - JWT 액세스/리프레시 토큰 생성 및 검증
2. **T027: Authentication Dependency** - 라우트 보호를 위한 미들웨어
3. **T028-031: Auth API 엔드포인트** - /auth/register, /auth/login, /auth/logout, /auth/refresh

UserService는 완성되었고, 다음 단계에서 JWT 토큰을 생성하고 API 엔드포인트에 연결할 예정입니다.
