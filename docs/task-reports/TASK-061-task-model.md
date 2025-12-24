# TASK-061: Task SQLAlchemy 모델 구현

**날짜**: 2025-12-24
**상태**: 완료
**TDD 사이클**: RED → GREEN → REFACTOR

---

## 무엇을 만들었나요?

학습 플랫폼에서 "학습 과제(Task)"를 저장하고 관리하기 위한 데이터베이스 모델을 만들었습니다.

쉽게 비유하자면, 학교에서 과목(Project)이 있고 그 안에 여러 개의 숙제(Task)가 있는 것처럼, 이 모델은 각 학습 프로젝트 안에 있는 개별 학습 과제를 표현합니다. 예를 들어 "Python 기초" 프로젝트 안에 "변수 이해하기", "조건문 배우기" 같은 과제들이 순서대로 정리됩니다.

---

## 왜 이렇게 만들었나요?

### 1. 순차 번호 (task_number)

각 과제에는 프로젝트 내에서 고유한 번호가 붙습니다. 첫 번째 과제는 1번, 두 번째는 2번... 이런 식입니다. 이 번호는 한번 정해지면 바꿀 수 없어서, 학습자가 자신의 진도를 명확하게 파악할 수 있습니다.

### 2. 소프트 삭제 (Soft Delete)

실수로 삭제해도 30일 동안은 휴지통에 보관됩니다. 컴퓨터의 휴지통처럼, 삭제해도 바로 사라지지 않고 복구할 기회가 있습니다.

### 3. 업로드 방식 추적

학습자가 코드를 어떻게 업로드했는지 기록합니다:
- `file`: 단일 파일 업로드
- `folder`: 폴더 업로드
- `paste`: 코드 붙여넣기

---

## 어떻게 작동하나요?

```python
# 새 과제 생성
task = Task(
    project_id=project.id,  # 어느 프로젝트에 속하는지
    task_number=1,           # 프로젝트 내 순서
    title="Python 변수 배우기"  # 과제 제목
)

# 과제 삭제 (휴지통으로 이동)
task.soft_delete()  # 30일 후 자동 삭제 예정

# 휴지통에서 복구
task.restore()  # 다시 활성 상태로
```

---

## TDD로 어떻게 테스트했나요?

### RED 단계 (실패하는 테스트 먼저 작성)
```
ModuleNotFoundError: No module named 'src.models.task'
```
Task 모델이 없는 상태에서 테스트를 실행하여 실패를 확인했습니다.

### GREEN 단계 (테스트 통과하도록 구현)
```
26 passed, 4 skipped
```
모든 핵심 테스트가 통과했습니다. (4개의 스킵은 PostgreSQL 전용 기능)

### REFACTOR 단계 (코드 품질 개선)
린트 검사 통과, 기존 모델과 일관된 패턴 유지로 리팩토링 불필요.

---

## 수정한 파일들

| 파일 | 변경 내용 |
|------|----------|
| `backend/src/models/task.py` | 새로 생성 - Task 모델 정의 |
| `backend/src/models/__init__.py` | Task 모델 export 추가 |
| `backend/src/models/project.py` | Project→Task 관계 추가 |
| `backend/tests/conftest.py` | Task 테이블 제약조건 처리 |
| `backend/tests/unit/test_task_model.py` | 새로 생성 - 30개 테스트 케이스 |

---

## 배운 개념들

### 1. SQLAlchemy ORM
객체와 데이터베이스 테이블을 연결해주는 도구입니다. Python 클래스로 데이터베이스를 다룰 수 있게 해줍니다.

### 2. 외래키 (Foreign Key)
"이 과제는 저 프로젝트에 속해있다"라는 관계를 표현합니다. `CASCADE` 옵션으로 프로젝트 삭제 시 관련 과제도 함께 삭제됩니다.

### 3. UNIQUE 제약조건
같은 프로젝트 안에서 같은 번호를 가진 과제가 생기지 않도록 데이터베이스 레벨에서 보장합니다.

---

## 주의사항

- 테스트는 SQLite를 사용하지만, 실제 운영에서는 PostgreSQL을 사용합니다
- PostgreSQL 전용 CHECK 제약조건(글자수 검증 등)은 SQLite 테스트에서 스킵됩니다
- task_number는 자동 증가가 아니라 서비스 레이어에서 관리해야 합니다

---

## 다음 단계

- [ ] T062: UploadedCode 모델 구현
- [ ] T063: CodeFile 모델 구현
- [ ] T068: TaskService 구현 (task_number 자동 증가 로직 포함)
