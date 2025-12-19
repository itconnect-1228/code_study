# Task 10: 데이터베이스 세션 관리

**완료일**: 2025-12-19
**관련 파일**: backend/src/db/session.py, backend/src/db/__init__.py

## 무엇을 만들었나요?

FastAPI 백엔드에서 PostgreSQL 데이터베이스에 연결하고 세션을 관리하는 시스템을 구현했습니다. 이것은 마치 도서관에서 책을 빌리고 반납하는 시스템과 같습니다 - 데이터베이스 연결을 미리 준비해두고, 필요할 때 빌려 쓰고, 다 쓰면 반납합니다.

## 왜 이렇게 만들었나요?

### 비동기(Async) 방식 선택
FastAPI는 비동기로 동작합니다. 마치 레스토랑에서 한 손님 주문을 받고 음식이 나올 때까지 기다리는 대신, 여러 손님의 주문을 동시에 받는 것과 같습니다.

### 연결 풀링(Connection Pooling)
매번 새로운 데이터베이스 연결을 만들면 느립니다. 대신 미리 10개의 연결을 만들어두고 재사용합니다. 마치 공유 자전거처럼요 - 필요할 때 빌리고, 다 쓰면 반납하면 다른 사람이 씁니다.

### FastAPI 의존성 주입
`Depends(get_session)`을 사용하면 매 요청마다 자동으로 세션이 생성되고 정리됩니다. 개발자가 매번 세션 생성/종료 코드를 작성할 필요가 없습니다.

## 어떻게 작동하나요?

1. **앱 시작 시**: `init_db()` 호출 → 연결 풀 생성
2. **API 요청 시**: `get_session()` → 풀에서 연결 하나 빌림 → 작업 수행 → 반납
3. **앱 종료 시**: `close_db()` 호출 → 모든 연결 해제

```python
# FastAPI 라우트에서 사용 예시
@app.get("/users")
async def get_users(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User))
    return result.scalars().all()
```

## 테스트는 어떻게 했나요?

- **RED**: 데이터베이스 연결 및 세션 관리 요구사항 정의
- **GREEN**: SQLAlchemy 2.0 async API를 사용하여 최소 구현 완료
- **REFACTOR**: 문서화 추가, `text()` 함수를 사용하여 raw SQL 처리 수정

## 수정된 파일

- `backend/src/db/session.py` - 세션 관리 핵심 로직 (약 260줄)
- `backend/src/db/__init__.py` - 패키지 exports
- `backend/src/__init__.py` - 소스 패키지 초기화
- `backend/__init__.py` - 백엔드 패키지 초기화

## 관련 개념

### ORM (Object-Relational Mapping)
SQL을 직접 쓰지 않고 Python 객체로 데이터베이스를 다루는 기술입니다.

### 컨텍스트 매니저
`async with`를 사용하면 작업이 끝난 후 자동으로 리소스가 정리됩니다.

### 의존성 주입
객체를 직접 만들지 않고 외부(FastAPI)에서 받아 사용하는 패턴입니다.

## 주의사항

1. `init_db()`는 앱 시작 시 한 번만 호출해야 합니다
2. 세션은 전역 변수로 재사용하면 안 됩니다 (각 요청은 독립적인 세션 필요)
3. 변경사항은 자동 커밋되지 않으므로 `await session.commit()` 필요
4. Windows에서는 asyncpg가 기본 이벤트 루프와 호환되지 않을 수 있음

## 다음 단계

- **T011**: 데이터베이스 설정 및 커넥션 풀링 (환경별 설정 관리)
- **T012-T017**: JWT, 비밀번호 해싱, FastAPI 앱 초기화 등 기본 인프라 구축
