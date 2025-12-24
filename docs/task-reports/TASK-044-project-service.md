# Task 044: ProjectService 구현

**완료일**: 2025-12-24
**관련 파일**:
- `backend/src/services/project_service.py` (생성)
- `backend/src/services/__init__.py` (수정)
- `backend/tests/unit/test_project_service.py` (생성)

## 무엇을 만들었나요?

프로젝트를 관리하는 서비스 클래스를 만들었습니다. 이 서비스는 프로젝트의 "CRUD" 작업을 담당합니다:

- **Create (생성)**: 새로운 학습 프로젝트를 만듭니다
- **Read (조회)**: 프로젝트를 ID로 찾거나, 사용자의 모든 프로젝트를 가져옵니다
- **Update (수정)**: 프로젝트 제목이나 설명을 변경합니다
- **Delete (삭제)**: 프로젝트를 휴지통으로 이동합니다 (30일 후 자동 삭제)

## 왜 이렇게 만들었나요?

**서비스 레이어 패턴을 사용한 이유:**

마트에서 물건을 사는 상황을 생각해보세요. 고객(API)이 직접 창고(데이터베이스)에 들어가서 물건을 가져오면 혼란스럽겠죠? 대신 점원(서비스)이 고객의 요청을 받아 창고에서 물건을 가져다 줍니다.

ProjectService가 바로 이 "점원" 역할을 합니다:
1. API 엔드포인트(고객)의 요청을 받습니다
2. 요청이 올바른지 검증합니다 (빈 제목인지, 사용자가 존재하는지 등)
3. 데이터베이스(창고)에서 작업을 수행합니다
4. 결과를 API에 돌려줍니다

**소프트 삭제(휴지통) 방식을 사용한 이유:**

컴퓨터의 휴지통처럼 작동합니다. 실수로 삭제해도 30일 동안은 복구할 수 있어요. 완전히 지우려면 휴지통을 비워야 합니다.

## 어떻게 작동하나요?

```python
# 프로젝트 생성
project = await service.create(
    user_id=user.id,
    title="파이썬 배우기",
    description="기초부터 시작하는 파이썬"
)

# 프로젝트 조회
project = await service.get_by_id(project_id)
projects = await service.get_by_user(user_id)  # 사용자의 모든 프로젝트

# 프로젝트 수정
updated = await service.update(project_id, title="새 제목")

# 휴지통으로 이동
await service.soft_delete(project_id)
```

## TDD 사이클

### 🔴 RED Phase
- 작성한 테스트: ProjectService의 CRUD 메서드에 대한 22개의 유닛 테스트
- 테스트 결과: ❌ 실패 (예상대로 - NotImplementedError 발생)
- **커밋**: `c64370c - test: T044 ProjectService - RED`

### 🟢 GREEN Phase
- 구현 내용: ProjectService 클래스의 create, get_by_id, get_by_user, update, soft_delete 메서드 구현
- 테스트 결과: ✅ 통과 (22개 모두 통과)
- **커밋**: `78b7f5a - feat: T044 ProjectService - GREEN`

### 🔵 REFACTOR Phase
- 개선 내용: 서비스 패키지 `__init__.py`에 ProjectService 익스포트 추가, 문서화 개선
- 테스트 결과: ✅ 여전히 통과
- **커밋**: `94d601c - refactor: T044 ProjectService - REFACTOR`

## 수정된 파일

| 파일 | 변경 내용 |
|------|----------|
| `backend/src/services/project_service.py` | 신규 생성 - ProjectService 클래스 구현 |
| `backend/src/services/__init__.py` | ProjectService 익스포트 추가 |
| `backend/tests/unit/test_project_service.py` | 신규 생성 - 22개 유닛 테스트 |

## 관련 개념

### 서비스 레이어 패턴
- API 핸들러와 데이터베이스 사이의 중간 계층
- 비즈니스 로직을 한 곳에 모아서 관리
- 테스트하기 쉽고 재사용 가능

### 소프트 삭제 (Soft Delete)
- 데이터를 바로 삭제하지 않고 "삭제됨" 표시만 함
- `deletion_status`: 'active' 또는 'trashed'
- `trashed_at`: 휴지통에 들어간 시간
- `scheduled_deletion_at`: 영구 삭제 예정 시간 (30일 후)

### 비동기 처리 (Async/Await)
- 데이터베이스 작업 중 다른 요청도 처리 가능
- `async def`와 `await` 키워드 사용
- SQLAlchemy의 AsyncSession 활용

## 주의사항

1. **사용자 검증**: 프로젝트 생성 시 user_id가 실제로 존재하는지 확인합니다
2. **제목 필수**: 빈 제목으로는 프로젝트를 만들거나 수정할 수 없습니다
3. **휴지통 확인**: `get_by_id()`는 기본적으로 휴지통의 프로젝트를 제외합니다
4. **중복 삭제 방지**: 이미 휴지통에 있는 프로젝트는 다시 삭제할 수 없습니다

## 다음 단계

- **T045**: 프로젝트 소유권 검증 구현 - 다른 사용자의 프로젝트에 접근 못하게
- **T046-T050**: 프로젝트 API 엔드포인트 구현 - REST API로 서비스 노출
