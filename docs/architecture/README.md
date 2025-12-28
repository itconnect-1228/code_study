# 프로젝트 아키텍처 설계도

AI Code Learning Platform의 시스템 아키텍처 문서입니다.

## 설계도 목록

### 1. [Backend Architecture](./backend-architecture.md)
FastAPI 기반 백엔드 서버의 내부 구조

- **API Layer**: FastAPI 라우터 (auth, projects, tasks, documents)
- **Dependencies**: 의존성 주입 (세션, 인증)
- **Schema Layer**: Pydantic 요청/응답 모델
- **Service Layer**: 비즈니스 로직 처리
- **Model Layer**: SQLAlchemy ORM 모델
- **Database**: PostgreSQL 연결 및 세션 관리
- **Celery**: 비동기 AI 문서 생성 태스크

---

### 2. [Frontend Architecture](./frontend-architecture.md)
React 기반 프론트엔드 애플리케이션 구조

- **App Structure**: React Router 라우팅 구조
- **Page Components**: Dashboard, ProjectDetail, TaskDetail 등
- **UI Components**: Layout, Project, Task, Document 컴포넌트
- **Service Layer**: API 클라이언트 및 서비스 함수
- **State Management**: Zustand + React Query

---

### 3. [System Architecture](./system-architecture.md)
전체 시스템 통합 배포 아키텍처

- **Deployment**: Netlify (Frontend) + Railway (Backend)
- **Data Flow**: 요청/응답 흐름
- **Authentication**: JWT 기반 인증 흐름
- **File Upload**: 코드 업로드 처리 흐름
- **AI Generation**: Gemini API 연동 흐름
- **CORS**: 교차 출처 설정
- **Environment**: 환경 변수 구성

---

## 기술 스택 요약

| 구분 | 기술 |
|------|------|
| **Frontend** | React 19.2, Vite, TypeScript, React Router v7, Zustand, React Query |
| **Backend** | FastAPI, SQLAlchemy (async), Celery, Redis |
| **Database** | PostgreSQL (asyncpg) |
| **AI** | Google Gemini API |
| **Hosting** | Netlify (Frontend), Railway (Backend + DB + Redis) |

---

## 다이어그램 형식

모든 설계도는 ASCII Art 형식으로 작성되어 있어 별도의 도구 없이 마크다운 뷰어에서 바로 확인할 수 있습니다.
