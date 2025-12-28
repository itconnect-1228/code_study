# Task 062: UploadedCode 모델 구현

**완료일**: 2025-12-24
**관련 파일**: backend/src/models/uploaded_code.py, backend/src/models/task.py, backend/src/models/__init__.py

---

## 무엇을 만들었나요?

사용자가 업로드한 코드의 **메타데이터**를 저장하는 SQLAlchemy 모델을 만들었습니다.

### UploadedCode란?

사용자가 학습할 코드를 업로드하면, 시스템은 그 코드에 대한 여러 정보를 분석합니다:
- **어떤 프로그래밍 언어**인지 (Python? JavaScript?)
- **얼마나 복잡한 코드**인지 (초보자용? 중급자용? 고급자용?)
- **총 몇 줄**인지
- **몇 개의 파일**인지
- **용량이 얼마**인지

이런 분석 결과를 저장하는 것이 UploadedCode 모델입니다.

**비유**: 도서관에 새 책이 도착하면, 책 자체는 서가에 보관하고, 책의 정보(저자, 페이지 수, 장르, 분류 번호)는 카탈로그 카드에 기록합니다. UploadedCode는 바로 이 **카탈로그 카드** 역할을 합니다.

---

## 왜 이렇게 만들었나요?

### 1. 일대일 관계 (One-to-One)

**하나의 Task에는 하나의 UploadedCode만** 연결됩니다.

**비유**: 주민등록증처럼, 한 사람에게 하나의 증명서만 발급되는 것과 같습니다. Task가 사람이라면, UploadedCode는 그 사람의 주민등록증입니다.

```python
task_id: Mapped[UUID] = mapped_column(
    ForeignKey("tasks.id", ondelete="CASCADE"),
    unique=True,  # 이 부분이 일대일 관계를 보장합니다
)
```

### 2. 10MB 용량 제한

업로드 용량을 **데이터베이스 레벨에서 강제**합니다.

**비유**: 엘리베이터에 최대 탑승 인원이 표시되어 있듯이, 업로드에도 최대 용량이 있습니다. 이 제한은 서버가 아닌 데이터베이스에서 직접 확인합니다.

```python
CheckConstraint(
    "upload_size_bytes IS NULL OR upload_size_bytes <= 10485760",
    name="valid_upload_size",
)
```

### 3. Cascade Delete

Task가 삭제되면 **UploadedCode도 자동으로 삭제**됩니다.

**비유**: 차를 폐차하면 차량등록증도 함께 폐기되는 것과 같습니다.

---

## 어떻게 작동하나요?

### 데이터 구조

```python
UploadedCode 테이블:
- id: 고유 번호 (UUID)
- task_id: 어느 Task의 코드인지 (Task 테이블 연결, 유일함)
- detected_language: 감지된 프로그래밍 언어 (예: "python", "javascript")
- complexity_level: 복잡도 수준 ("beginner", "intermediate", "advanced")
- total_lines: 총 코드 줄 수
- total_files: 업로드된 파일 수
- upload_size_bytes: 총 용량 (바이트 단위)
- created_at: 업로드 시각
```

### 유틸리티 속성

모델에 편리한 유틸리티를 추가했습니다:

```python
# 용량을 MB 단위로 확인
uploaded_code.size_mb  # 예: 0.5 (500KB)

# 용량이 제한 이내인지 확인
uploaded_code.is_size_valid  # True 또는 False

# 용량 검증 (에러 발생)
uploaded_code.validate_size()  # ValueError if > 10MB
```

### 복잡도 수준

코드 복잡도는 세 단계로 분류됩니다:

| 수준 | 설명 |
|------|------|
| beginner | 기초 문법, 간단한 로직 |
| intermediate | 함수, 클래스, 모듈 활용 |
| advanced | 복잡한 알고리즘, 디자인 패턴 |

---

## 수정된 파일

| 파일 | 설명 |
|------|------|
| [backend/src/models/uploaded_code.py](backend/src/models/uploaded_code.py) | UploadedCode SQLAlchemy 모델 (신규) |
| [backend/src/models/task.py](backend/src/models/task.py) | Task 모델에 uploaded_code 관계 추가 |
| [backend/src/models/__init__.py](backend/src/models/__init__.py) | UploadedCode export 추가 |

---

## 관련 개념

### 1. SQLAlchemy ORM
Python에서 데이터베이스를 객체처럼 다룰 수 있게 해주는 도구입니다. SQL 쿼리를 직접 작성하지 않고도 데이터를 저장하고 불러올 수 있습니다.

### 2. 외래 키 (Foreign Key)
두 테이블을 연결하는 열쇠입니다. UploadedCode의 task_id는 Tasks 테이블의 id를 가리킵니다.

### 3. 데이터베이스 제약조건 (Constraints)
데이터의 무결성을 보장하는 규칙입니다. 예를 들어, 용량이 10MB를 초과하면 저장이 거부됩니다.

### 4. UUID (Universally Unique Identifier)
전 세계적으로 고유한 식별자입니다. 여러 서버에서 동시에 데이터를 생성해도 ID가 충돌하지 않습니다.

---

## 주의사항

### 실제 코드 파일은 별도 저장

UploadedCode는 **메타데이터만** 저장합니다. 실제 코드 파일 내용은:
- 데이터베이스가 아닌 파일 시스템에 저장됩니다
- CodeFile 모델(T063)에서 파일 경로를 관리합니다

### NULL 허용 필드

분석이 완료되기 전에는 detected_language, complexity_level 등이 NULL일 수 있습니다. 업로드 직후에는 메타데이터가 아직 계산되지 않았기 때문입니다.

---

## 다음 단계

Task 062 완료 후 다음 작업:

1. **T063: CodeFile 모델 구현** - 개별 코드 파일 정보 저장
2. **T064: 파일 검증 유틸리티** - 확장자, 크기, 바이너리 검증
3. **T065: 언어 감지 서비스** - Pygments로 프로그래밍 언어 자동 감지

UploadedCode 모델은 코드 업로드 기능의 기반이며, 이후 학습 문서 생성에 필요한 메타데이터를 제공합니다.
