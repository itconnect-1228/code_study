# TASK-063: CodeFile SQLAlchemy 모델 생성

**작성일**: 2025-12-25
**태스크 ID**: T063
**상태**: 완료 ✅

## 무엇을 만들었나요?

코드 파일 정보를 저장하는 `CodeFile` 모델을 만들었습니다. 사용자가 코드를 업로드하면 여러 개의 파일이 있을 수 있는데, 각 파일마다 따로 정보를 저장해야 하잖아요? 그래서 이 모델이 필요합니다.

쉽게 비유하자면, 학교 사물함(UploadedCode)에 여러 개의 책(CodeFile)을 넣는 것과 같아요. 사물함 하나에 책 여러 권이 들어가듯, 한 번의 업로드에 여러 파일이 포함될 수 있습니다.

## 왜 이렇게 만들었나요?

### 1. 파일별 정보 추적
폴더를 업로드하면 여러 파일이 한꺼번에 올라옵니다. 각 파일의 이름, 위치, 크기, 확장자를 개별적으로 저장해야 나중에 "어떤 파일이 어디 있지?" 하고 찾을 수 있어요.

### 2. 허용 확장자 제한
`.py`, `.js`, `.ts` 같은 코드 파일만 허용합니다. 바이러스가 들어있을 수 있는 `.exe` 같은 실행 파일은 막아야 하니까요.

### 3. UploadedCode와 연결
한 번의 업로드(`UploadedCode`)에 여러 파일(`CodeFile`)이 연결됩니다. 부모가 삭제되면 자식도 같이 삭제되도록 CASCADE 삭제를 설정했어요.

## 어떻게 작동하나요?

```python
# 코드 파일 저장 예시
code_file = CodeFile(
    uploaded_code_id=uploaded_code.id,  # 어떤 업로드에 속하는지
    file_name="main.py",                 # 원본 파일명
    file_path="src/main.py",             # 폴더 내 경로
    file_extension=".py",                # 확장자
    file_size_bytes=1024,                # 파일 크기
    storage_path="storage/uploads/abc/def/xyz.py",  # 실제 저장 위치
    mime_type="text/x-python"            # MIME 타입
)
```

## 테스트는 어떻게 했나요?

### TDD 사이클
1. **RED**: 모델이 없는 상태에서 import 시도 → 실패 확인
2. **GREEN**: 모델 생성 후 import 성공
3. **REFACTOR**: 코드 정리 및 docstring 추가

### 구조 검증
- 모든 필드가 data-model.md 스키마와 일치하는지 확인
- CHECK 제약조건(지원 확장자)이 올바르게 정의되었는지 확인
- 관계(relationship)가 양방향으로 설정되었는지 확인

## 수정된 파일들

| 파일 | 변경 내용 |
|------|----------|
| `backend/src/models/code_file.py` | 신규 생성 - CodeFile 모델 |
| `backend/src/models/__init__.py` | CodeFile 추가 export |
| `backend/src/models/uploaded_code.py` | code_files relationship 추가 |

## 관련 개념

### SQLAlchemy Relationship
두 테이블을 연결하는 방법입니다. `relationship()`을 사용하면 Python 객체처럼 연결된 데이터에 접근할 수 있어요.

```python
# UploadedCode에서 연결된 모든 파일 가져오기
for file in uploaded_code.code_files:
    print(file.file_name)
```

### Cascade Delete
부모 레코드가 삭제되면 자식도 같이 삭제합니다. 업로드가 삭제되면 관련 파일 정보도 자동으로 삭제됩니다.

### CHECK Constraint
데이터베이스 레벨에서 값을 검증합니다. 지원하지 않는 확장자(.exe 등)로 파일을 저장하려고 하면 데이터베이스가 거부합니다.

## 주의사항

1. **파일 개수 제한**: 업로드당 1-20개 파일만 허용 (FR-018) - 서비스 레이어에서 검증 필요
2. **storage_path는 필수**: 실제 파일이 어디 저장됐는지 반드시 기록해야 합니다
3. **바이너리 파일 차단**: MIME 타입 검사로 텍스트 파일만 허용해야 합니다 (FR-016)

## 다음 단계

- T064: 파일 검증 유틸리티 구현 (확장자, 크기, 바이너리 감지)
- T065: 언어 감지 서비스 구현 (Pygments 사용)
- T066: 코드 복잡도 분석기 구현
