# TASK-090: LearningDocument SQLAlchemy 모델 생성

**완료일**: 2025-12-26
**관련 파일**:
- [backend/src/models/learning_document.py](backend/src/models/learning_document.py)
- [backend/src/models/__init__.py](backend/src/models/__init__.py)
- [backend/src/models/task.py](backend/src/models/task.py)

---

## 무엇을 만들었나요?

**학습 문서 모델**을 만들었습니다. 이건 마치 **교과서를 담는 책장**과 같아요.

AI가 사용자의 코드를 분석해서 만든 7개 챕터짜리 학습 교재를 저장하는 곳이에요. 책장에 책을 꽂아두면 나중에 언제든 꺼내 읽을 수 있듯이, AI가 만든 교재도 여기에 저장해두면 언제든 다시 볼 수 있어요.

---

## 왜 이렇게 만들었나요?

### 1. JSONB로 7챕터 구조 저장

PostgreSQL의 **JSONB** 타입을 사용했어요. 이건 마치 **여러 칸이 있는 서랍장**과 같아요.

- 챕터1: 코드가 뭘 하는지 한 줄 요약
- 챕터2: 미리 알아야 할 개념들
- 챕터3: 코드 구조 살펴보기
- 챕터4: 한 줄 한 줄 설명
- 챕터5: 실행 순서 따라가기
- 챕터6: 핵심 개념 정리
- 챕터7: 흔히 하는 실수들

각 챕터를 따로 저장하면 나중에 특정 챕터만 빠르게 가져올 수 있어요.

### 2. 생성 상태 추적

문서 생성은 시간이 걸려요. 그래서 상태를 추적해요:
- `pending`: 아직 시작 안 함 (대기 중인 주문)
- `in_progress`: 생성 중 (요리 중)
- `completed`: 완료 (배달 완료)
- `failed`: 실패 (문제 발생)

### 3. Celery 태스크 연동

AI 문서 생성은 **비동기**로 처리돼요. 마치 배달 앱에서 주문하면 주문번호(celery_task_id)를 받고, 그 번호로 배달 상태를 확인하는 것과 같아요.

---

## 어떻게 동작하나요?

```
사용자가 코드 업로드
        ↓
    Task 생성됨
        ↓
LearningDocument 생성 (status: pending)
        ↓
Celery가 AI 문서 생성 시작 (status: in_progress)
        ↓
    AI가 7챕터 생성
        ↓
LearningDocument에 저장 (status: completed)
        ↓
사용자가 문서 조회 가능
```

---

## 테스트는 어떻게 했나요?

1. **모델 정의 확인**: 기존 Task, UploadedCode 모델과 동일한 패턴 사용
2. **관계 설정 확인**: Task와 1:1 관계 설정 완료
3. **타입 힌트 확인**: Mapped[] 타입으로 정적 타입 검사 가능

---

## 수정한 파일들

| 파일 | 변경 내용 |
|------|-----------|
| `learning_document.py` | 새 모델 생성 (약 250줄) |
| `__init__.py` | LearningDocument 내보내기 추가 |
| `task.py` | learning_document 관계 추가 |

---

## 관련 개념

- **SQLAlchemy ORM**: Python 객체를 데이터베이스 테이블과 매핑
- **JSONB**: PostgreSQL의 바이너리 JSON 타입 (일반 JSON보다 빠름)
- **relationship()**: 테이블 간 관계 정의
- **Celery**: 비동기 작업 처리 도구

---

## 주의사항

1. **content 검증**: DB 레벨에서 7챕터 구조 검증 제약조건은 별도 마이그레이션 필요
2. **마이그레이션**: 이 모델을 실제 DB에 적용하려면 Alembic 마이그레이션 실행 필요
3. **Task 관계**: Task 삭제 시 LearningDocument도 함께 삭제됨 (CASCADE)

---

## 다음 단계

- T091: Gemini API 클라이언트 래퍼 구현
- T092: 7챕터 문서 생성 프롬프트 템플릿 작성
- T093: DocumentGenerationService 구현
