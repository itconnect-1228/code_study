# Task 011: 데이터베이스 설정 관리 모듈

**완료일**: 2025-12-19
**관련 파일**:
- `backend/src/db/config.py` (생성)
- `backend/src/db/session.py` (수정)
- `backend/src/db/__init__.py` (수정)
- `backend/tests/unit/test_db_config.py` (생성)

## 무엇을 만들었나요?

데이터베이스 연결 설정을 전담하는 독립적인 모듈을 만들었습니다. 마치 집의 전기 배선함처럼, 모든 데이터베이스 연결 정보를 한 곳에서 관리합니다.

주요 구성요소:
- **PoolConfig**: 연결 풀 설정 (택시 정류장에서 대기하는 택시 수 관리)
- **DatabaseConfig**: 전체 데이터베이스 설정 (주소, 사용자명, 비밀번호 등)
- **get_database_config()**: 환경 변수에서 설정을 읽어오는 함수

## 왜 이렇게 만들었나요?

기존 `session.py`에서는 데이터베이스 URL 생성 로직이 세션 관리 코드와 섞여 있었습니다. 이것은 마치 요리사가 재료 구매와 요리를 동시에 하는 것과 같습니다.

**관심사의 분리(Separation of Concerns)** 원칙을 적용해서:
- `config.py`: 설정 정보 관리 (재료 구매 담당)
- `session.py`: 실제 연결 생성 및 관리 (요리 담당)

이렇게 분리하면:
1. 설정만 따로 테스트할 수 있습니다
2. 설정 변경 시 연결 로직을 건드릴 필요가 없습니다
3. 코드를 읽고 이해하기 쉬워집니다

## 어떻게 작동하나요?

### 1단계: 환경 변수에서 설정 읽기
```python
config = get_database_config()
# DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD 등을 읽어옴
```

### 2단계: 연결 URL 생성
```python
url = config.get_connection_url()
# 결과: postgresql+asyncpg://user:pass@localhost:5432/mydb
```

특수문자가 포함된 비밀번호는 자동으로 안전하게 변환됩니다:
- `@` → `%40`
- `#` → `%23`

### 3단계: 세션 초기화에서 사용
```python
init_db()  # 자동으로 config를 로드해서 사용
# 또는
init_db(config=custom_config)  # 직접 config 전달
```

## 테스트는 어떻게 했나요?

### 🔴 RED 단계
29개의 테스트를 먼저 작성했습니다:
- PoolConfig 기본값/커스텀 값 테스트
- DatabaseConfig URL 생성 테스트
- 환경 변수 로딩 테스트
- 특수문자 인코딩 테스트
- 에러 처리 테스트

### 🟢 GREEN 단계
테스트를 통과하는 최소한의 코드를 작성했습니다:
- 데이터클래스로 설정 구조 정의
- URL 인코딩 로직 구현
- 환경 변수 파싱 로직 구현

**결과**: 29개 테스트 모두 통과!

### 🔵 REFACTOR 단계
- `session.py`에서 중복 코드 제거
- `init_db()`가 config 객체를 직접 받을 수 있도록 개선
- `get_current_config()` 함수 추가로 현재 설정 조회 가능

## 수정된 파일

| 파일 | 변경 내용 |
|------|----------|
| `backend/src/db/config.py` | 새로 생성 - 설정 관리 모듈 |
| `backend/src/db/session.py` | config 모듈 사용하도록 수정 |
| `backend/src/db/__init__.py` | 새 exports 추가 |
| `backend/tests/unit/test_db_config.py` | 29개 단위 테스트 |
| `backend/tests/__init__.py` | 테스트 패키지 초기화 |
| `backend/tests/unit/__init__.py` | 단위 테스트 패키지 초기화 |

## 관련 개념

### 연결 풀(Connection Pool)
데이터베이스 연결은 생성 비용이 높습니다. 매번 새로 만드는 대신 미리 여러 개를 만들어두고 필요할 때 빌려쓰는 방식입니다. 렌터카처럼요!

- `pool_size=10`: 평상시 10개 연결 유지
- `max_overflow=20`: 바쁠 때 20개 더 생성 가능
- `pool_timeout=30`: 30초 기다려도 연결 못 받으면 에러

### URL 인코딩
웹 주소에서 특수문자를 안전하게 표현하는 방법입니다. 우편번호에 특수문자를 쓸 수 없어서 변환하는 것과 비슷합니다.

## 주의사항

1. **필수 환경 변수**: `DB_HOST`, `DB_NAME`, `DB_USER`는 반드시 설정해야 합니다
2. **비밀번호 보안**: `.env` 파일은 절대 Git에 올리지 마세요
3. **DATABASE_URL 우선**: 전체 URL이 설정되면 개별 변수보다 우선합니다

## 다음 단계

Phase 2 기반 인프라 작업 계속:
- T012: JWT 토큰 유틸리티
- T013: 비밀번호 해싱 유틸리티
- T014: FastAPI 앱 초기화
