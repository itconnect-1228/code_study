# TASK-084: 단일 파일 업로드로 태스크 생성 테스트

**작성일**: 2025년 12월 26일
**테스트 방법**: Playwright MCP 브라우저 자동화
**테스트 결과**: ✅ 통과 (백엔드) / ⚠️ 프론트엔드 렌더링 버그 발견

---

## 무엇을 테스트했나요?

사용자가 프로젝트에서 Python 코드 파일을 업로드하여 새 학습 태스크를 만들 때, 시스템이 올바르게 "Task 1" 번호를 부여하는지 확인했습니다.

---

## 왜 이 테스트가 중요한가요?

마치 도서관에서 책에 고유번호를 붙이는 것처럼, 각 학습 태스크에도 순서대로 번호가 부여되어야 합니다. 첫 번째로 만든 태스크는 "Task 1", 두 번째는 "Task 2"가 되어야 사용자가 자신의 학습 진행 상황을 쉽게 파악할 수 있습니다.

---

## 테스트 과정

### 1단계: 테스트 환경 준비
- 프론트엔드 서버 (localhost:3000) 시작
- 백엔드 서버 (localhost:8000) 시작
- 환경변수 설정 수정 (localhost 일관성 확보)

### 2단계: 사용자 등록 및 로그인
- 테스트 계정 생성: `task84_test@example.com`
- 비밀번호: `TestPass123!`
- 로그인 후 대시보드 접근 확인

### 3단계: 프로젝트 생성
- 프로젝트명: "TASK 84 테스트 프로젝트"
- 생성 성공 확인

### 4단계: 태스크 생성 (핵심 테스트)
- 태스크 제목: "Python 기초 함수 학습"
- 업로드 파일: `test_upload.py` (Python 기초 함수 예제 코드)
- 업로드 방법: 단일 파일 업로드

### 5단계: 결과 검증
API 응답 확인:
```json
{
  "status": 200,
  "data": [
    {
      "id": "e39ca239-5172-4475-a6b3-0c1dbdf99fe7",
      "project_id": "b33d19aa-9333-4e20-83fb-e103a4dd1be4",
      "task_number": 1,
      "title": "Python 기초 함수 학습",
      "upload_method": "file",
      "deletion_status": "active"
    }
  ]
}
```

---

## 테스트 결과

### ✅ 백엔드 테스트 통과

| 검증 항목 | 기대값 | 실제값 | 결과 |
|-----------|--------|--------|------|
| 태스크 생성 | 201 Created | 201 Created | ✅ |
| task_number | 1 | 1 | ✅ |
| upload_method | "file" | "file" | ✅ |
| deletion_status | "active" | "active" | ✅ |

### ⚠️ 발견된 버그

**프론트엔드 렌더링 이슈**: 태스크가 백엔드에서 정상 생성되었으나, UI에서 태스크 목록이 표시되지 않음.

- API는 올바른 데이터 반환 (200 OK)
- UI는 "아직 태스크가 없습니다" 메시지 표시
- 원인 추정: React Query 캐시 갱신 또는 상태 관리 문제

**권장 조치**: 프론트엔드 태스크 목록 컴포넌트의 데이터 페칭 로직 검토 필요

---

## 테스트에 사용된 파일

### 업로드한 Python 파일 (`test_upload.py`)
```python
# Python 기초 함수 예제
def greet(name):
    """인사말을 반환하는 함수"""
    return f"안녕하세요, {name}님!"

def add(a, b):
    """두 숫자를 더하는 함수"""
    return a + b

if __name__ == "__main__":
    print(greet("홍길동"))
    print(add(3, 5))
```

---

## 관련 파일

- 백엔드 태스크 API: [backend/src/api/tasks.py](../../backend/src/api/tasks.py)
- 태스크 서비스: [backend/src/services/task_service.py](../../backend/src/services/task_service.py)
- 프론트엔드 프로젝트 상세: [frontend/src/pages/ProjectDetail.tsx](../../frontend/src/pages/ProjectDetail.tsx)

---

## 다음 단계

1. **T085**: 폴더 업로드 테스트 - 폴더 구조가 보존되는지 확인
2. **T086**: 붙여넣기 업로드 테스트 - 언어 자동 감지 확인
3. **프론트엔드 버그 수정**: 태스크 목록 렌더링 이슈 해결

---

## TDD 사이클 기록

- 🔴 **RED**: 태스크 생성 및 번호 부여 테스트 케이스 정의
- 🟢 **GREEN**: 백엔드 API가 task_number=1로 올바르게 반환
- 🔵 **REFACTOR**: 프론트엔드 렌더링 버그 발견 - 별도 이슈로 처리 필요
