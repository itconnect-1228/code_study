# TASK-001 ~ T009: 프로젝트 초기 설정

**날짜**: 2025-12-24 (문서 정리)
**상태**: 완료
**태스크**: T001, T001A, T002, T003, T004, T005, T006, T007, T008, T009

---

## 무엇을 만들었나요?

프로젝트의 기초 뼈대를 세웠습니다. 집을 짓기 전에 땅을 다지고, 기둥을 세우고, 전기와 수도 배관을 설치하는 것처럼, 코드를 작성하기 전에 필요한 모든 준비 작업을 완료했습니다.

---

## 포함된 태스크

### Phase 1: Setup (프로젝트 구조)

| Task | 설명 | 파일/폴더 |
|------|------|-----------|
| T001 | 디렉토리 구조 생성 | `backend/`, `frontend/`, `storage/`, `docs/` |
| T001A | 태스크 보고서 디렉토리 | `docs/task-reports/` |
| T002 | 백엔드 Python 프로젝트 초기화 | `backend/requirements.txt` |
| T003 | 프론트엔드 React 프로젝트 초기화 | `frontend/` (Vite + TypeScript) |
| T004 | Docker Compose 설정 | `docker-compose.yml` (PostgreSQL, Redis) |
| T005 | 환경 변수 템플릿 | `.env.example` |
| T006 | 린터/포맷터 설정 | Ruff, Black (Python) / ESLint, Prettier (TS) |
| T007 | Git ignore 패턴 | `.gitignore` |

### Phase 2: Database & Migrations (데이터베이스 설정)

| Task | 설명 | 파일/폴더 |
|------|------|-----------|
| T008 | Alembic 마이그레이션 프레임워크 | `backend/alembic/` |
| T009 | 초기 데이터베이스 스키마 | `backend/alembic/versions/001_initial_schema.py` |

---

## 왜 이렇게 만들었나요?

### 1. 명확한 디렉토리 구조
- **backend/**: Python FastAPI 서버 코드
- **frontend/**: React TypeScript 클라이언트 코드
- **storage/uploads/**: 사용자 업로드 파일 저장
- **docs/**: 문서 및 태스크 보고서

### 2. Docker로 개발 환경 통일
모든 개발자가 같은 환경에서 작업할 수 있도록 PostgreSQL과 Redis를 Docker 컨테이너로 실행합니다.

### 3. Alembic으로 데이터베이스 버전 관리
데이터베이스 스키마 변경을 코드로 관리하여, 팀원들과 쉽게 동기화할 수 있습니다.

---

## 프로젝트 구조

```
code_study/
├── backend/
│   ├── src/
│   │   ├── api/          # REST API 엔드포인트
│   │   ├── db/           # 데이터베이스 연결
│   │   ├── models/       # SQLAlchemy 모델
│   │   ├── services/     # 비즈니스 로직
│   │   ├── tasks/        # Celery 백그라운드 작업
│   │   └── utils/        # 유틸리티 함수
│   ├── tests/            # 테스트 코드
│   ├── alembic/          # DB 마이그레이션
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React 컴포넌트
│   │   ├── pages/        # 페이지 컴포넌트
│   │   ├── services/     # API 클라이언트
│   │   ├── stores/       # Zustand 상태 관리
│   │   └── hooks/        # 커스텀 훅
│   └── package.json
├── storage/uploads/      # 파일 업로드 저장소
├── docs/task-reports/    # 태스크 보고서
└── docker-compose.yml
```

---

## 주요 의존성

### Backend (Python)
- FastAPI: 웹 프레임워크
- SQLAlchemy 2.0: ORM
- Alembic: 마이그레이션
- Celery + Redis: 비동기 작업
- pytest: 테스트

### Frontend (TypeScript)
- React 18: UI 라이브러리
- Vite: 빌드 도구
- TanStack Query: 서버 상태 관리
- Zustand: 클라이언트 상태 관리
- Tailwind CSS: 스타일링

---

## 다음 단계

- T010-T022: 기반 인프라 구축 (DB 연결, JWT, 라우터 등)
