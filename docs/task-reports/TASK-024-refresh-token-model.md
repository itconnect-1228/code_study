# Task 024: RefreshToken 모델 구현

**완료일**: 2025-12-22
**관련 파일**: backend/src/models/refresh_token.py, backend/tests/unit/test_refresh_token_model.py

---

## 무엇을 만들었나요?

JWT 인증 시스템에서 사용하는 **리프레시 토큰**을 데이터베이스에 저장하고 관리하는 SQLAlchemy 모델을 만들었습니다.

### 리프레시 토큰이란?

웹사이트에 로그인하면 보통 두 가지 열쇠를 받습니다:
- **액세스 토큰** (짧은 열쇠): 15분만 사용 가능한 일회용 출입증
- **리프레시 토큰** (긴 열쇠): 7일간 사용 가능한 마스터 키

리프레시 토큰은 액세스 토큰이 만료되면 새로운 액세스 토큰을 발급받는 데 사용됩니다. 만약 누군가 액세스 토큰을 훔쳐가도 15분 후면 무용지물이 되고, 리프레시 토큰이 없으면 새 열쇠를 만들 수 없습니다.

---

## 왜 이렇게 만들었나요?

### 1. 보안을 위한 해시 저장

**실제 토큰 값을 그대로 저장하지 않고 SHA-256 해시로 변환해서 저장**합니다.

**비유**: 은행 금고의 비밀번호를 직접 적어두지 않고, 암호화된 힌트만 저장하는 것과 같습니다. 데이터베이스가 해킹당해도 실제 토큰을 알아낼 수 없습니다.

### 2. 토큰 순환 (Token Rotation)

새 토큰을 발급할 때마다 **이전 토큰은 폐기(revoke)**합니다.

**비유**: 호텔 룸키를 재발급받으면 이전 키카드는 자동으로 무효화되는 것과 같습니다.

### 3. 자동 삭제 (Cascade Delete)

사용자가 탈퇴하면 **그 사용자의 모든 리프레시 토큰도 자동으로 삭제**됩니다.

**비유**: 회사를 퇴사하면 사원증과 함께 모든 출입 기록도 자동으로 제거되는 것과 같습니다.

---

## 어떻게 작동하나요?

### 데이터 구조

```python
RefreshToken 테이블:
- id: 토큰 고유 번호 (UUID)
- user_id: 어느 사용자의 토큰인지 (User 테이블 연결)
- token_hash: 토큰의 암호화된 값 (SHA-256)
- expires_at: 언제 만료되는지 (생성 후 7일)
- created_at: 언제 만들어졌는지
- revoked: 폐기되었는지 (True/False)
- revoked_at: 언제 폐기되었는지
```

### 유틸리티 속성

- `is_expired`: 토큰이 만료되었는지 확인
- `is_valid`: 토큰이 유효한지 확인 (만료되지 않고 폐기되지 않음)

### 성능 최적화 인덱스

세 가지 인덱스를 추가하여 빠른 검색을 지원합니다:

1. **idx_refresh_tokens_user_id**: 사용자의 모든 토큰을 빠르게 조회
2. **idx_refresh_tokens_hash**: 토큰 검증 시 빠른 조회
3. **idx_refresh_tokens_expires**: 만료된 토큰 정리 작업 최적화

---

## TDD 사이클

### 🔴 RED Phase
- 작성한 테스트: RefreshToken 모델 생성, 제약 조건, 기본값, 관계, __repr__ 테스트 (13개)
- 테스트 결과: ❌ 실패 (ModuleNotFoundError - 모델이 없음)
- **커밋**: `f73a7e9 - test: T024 RefreshToken model - RED`

### 🟢 GREEN Phase
- 구현 내용: RefreshToken SQLAlchemy 모델 구현, __init__.py 및 conftest.py 업데이트
- 테스트 결과: ✅ 13개 테스트 통과
- **커밋**: `11ea09d - feat: T024 RefreshToken model - GREEN`

### 🔵 REFACTOR Phase
- 개선 내용: is_expired, is_valid 유틸리티 속성 추가 및 테스트 5개 추가
- 테스트 결과: ✅ 18개 테스트 모두 통과
- **커밋**: `b7fe1ba - refactor: T024 RefreshToken model - REFACTOR`

---

## 수정된 파일

| 파일 | 설명 |
|------|------|
| backend/src/models/refresh_token.py | RefreshToken SQLAlchemy 모델 (신규) |
| backend/src/models/__init__.py | RefreshToken export 추가 |
| backend/tests/conftest.py | RefreshToken import 추가 |
| backend/tests/unit/test_refresh_token_model.py | 18개 테스트 케이스 (신규) |

---

## 관련 개념

### 1. JWT (JSON Web Token)
웹 인증에서 사용하는 토큰 형식입니다. 토큰 안에 사용자 정보가 암호화되어 들어있습니다.

### 2. SHA-256 해시
데이터를 고정된 길이의 암호화된 문자열로 변환하는 알고리즘입니다. 같은 입력은 항상 같은 출력을 만들지만, 출력에서 입력을 역추적할 수 없습니다.

### 3. CASCADE DELETE
데이터베이스에서 부모 레코드가 삭제되면 자식 레코드도 자동으로 삭제되는 기능입니다.

### 4. 데이터베이스 인덱스
책의 색인과 같이, 특정 컬럼으로 데이터를 빠르게 찾을 수 있도록 돕는 구조입니다.

---

## 주의사항

### SQLite 테스트 환경 제약

테스트에서는 SQLite 메모리 데이터베이스를 사용하는데, 몇 가지 제약사항이 있습니다:

1. **CASCADE DELETE 미작동**: SQLite는 기본적으로 외래 키 제약을 강제하지 않습니다. 따라서 CASCADE DELETE 테스트는 모델 정의만 확인합니다.
2. **타임존 처리**: SQLite는 타임존 정보를 저장하지 않으므로 테스트에서 타임존을 제거한 후 비교합니다.

**프로덕션 환경(PostgreSQL)에서는 이러한 제약이 없으며 모든 기능이 정상 작동합니다.**

### 보안 고려사항

1. **절대 원본 토큰을 저장하지 마세요**: token_hash만 저장합니다.
2. **만료된 토큰은 정기적으로 삭제**: 배경 작업으로 주기적으로 정리해야 합니다.
3. **폐기된 토큰 검증**: 토큰 사용 시 revoked 상태를 반드시 확인해야 합니다.

---

## 다음 단계

Task 024 완료 후 다음 작업:

1. **T025: UserService 구현** - 회원가입, 로그인, 로그아웃 로직
2. **T026: TokenService 구현** - 토큰 생성, 검증, 순환 로직
3. **T027: 인증 dependency 구현** - 라우트 보호를 위한 미들웨어

RefreshToken 모델은 이제 완성되었고, 다음 단계에서 실제로 이 모델을 사용하는 서비스 로직을 구현할 예정입니다.
