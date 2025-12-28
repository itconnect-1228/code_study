# System Architecture

AI Code Learning Platform - 전체 시스템 통합 배포 아키텍처

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        SYSTEM ARCHITECTURE                                    ║
║                     AI Code Learning Platform                                 ║
║                   Frontend + Backend Integration                              ║
╚══════════════════════════════════════════════════════════════════════════════╝


┌──────────────────────────────────────────────────────────────────────────────┐
│                          Deployment Architecture                              │
│                         (Railway 통합 배포)                                   │
└──────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │     Client      │
                              │  (Web Browser)  │
                              └────────┬────────┘
                                       │
                                       │ HTTPS
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                               Railway                                         │
│                    (Frontend + Backend 통합 호스팅)                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │                      Frontend Service                                 │    │
│  │                      (Static Files)                                   │    │
│  ├──────────────────────────────────────────────────────────────────────┤    │
│  │                                                                       │    │
│  │   • React SPA (dist/)                                                 │    │
│  │   • index.html                                                        │    │
│  │   • JavaScript bundles                                                │    │
│  │   • CSS files                                                         │    │
│  │   • Assets (images, fonts)                                            │    │
│  │                                                                       │    │
│  │   Build: npm run build                                                │    │
│  │   Serve: serve -s dist (또는 nginx)                                   │    │
│  │                                                                       │    │
│  │   URL: https://your-app.railway.app                                   │    │
│  │                                                                       │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                       │                                       │
│                                       │ API Calls (Same Origin)               │
│                                       ▼                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐    │
│  │                  │  │                  │  │                          │    │
│  │  Backend API     │  │  Celery Worker   │  │      Databases           │    │
│  │  (FastAPI)       │  │  (Optional)      │  │                          │    │
│  │                  │  │                  │  │  ┌──────────────────┐    │    │
│  │  Port: 8000      │  │  AI 문서 생성    │  │  │   PostgreSQL     │    │    │
│  │                  │  │  비동기 처리     │  │  │                  │    │    │
│  │  Endpoints:      │  │                  │  │  │  • users         │    │    │
│  │  • /api/v1/auth  │◄─┤  Celery Task:    │  │  │  • projects      │    │    │
│  │  • /api/v1/      │  │  generate_       │  │  │  • tasks         │    │    │
│  │    projects      │  │  learning_       │  │  │  • uploaded_codes│    │    │
│  │  • /api/v1/tasks │  │  document()      │  │  │  • code_files    │    │    │
│  │  • /api/v1/      │  │                  │  │  │  • learning_docs │    │    │
│  │    documents     │  │                  │  │  │                  │    │    │
│  │                  │  │                  │  │  └──────────────────┘    │    │
│  │                  │  │                  │  │                          │    │
│  │                  │  │                  │  │  ┌──────────────────┐    │    │
│  │                  │  │                  │  │  │      Redis       │    │    │
│  │                  │  │                  │  │  │                  │    │    │
│  └────────┬─────────┘  └────────┬─────────┘  │  │  • Celery Broker │    │    │
│           │                     │            │  │  • Result Backend│    │    │
│           │                     │            │  │                  │    │    │
│           │   Internal Network  │            │  └──────────────────┘    │    │
│           │   (*.railway.internal)           │                          │    │
│           └─────────────────────┼────────────┴──────────────────────────┘    │
│                                 │                                             │
│  URL: https://your-api.railway.app                                           │
│                                                                               │
│  Pricing: $5/월 (Hobby Plan, $5 크레딧 포함)                                 │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┬─┘
                                                                               │
                                                                               │ External API
                                                                               ▼
                                              ┌────────────────────────────────┐
                                              │       Google Gemini API        │
                                              ├────────────────────────────────┤
                                              │                                │
                                              │  AI 학습 문서 생성             │
                                              │  • 코드 분석                   │
                                              │  • 7장 구조 문서 생성          │
                                              │                                │
                                              │  Rate Limit: 분당 60 요청      │
                                              │  Retry: 지수 백오프            │
                                              │                                │
                                              └────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                        Railway Services Structure                             │
│                         (Railway 서비스 구조)                                 │
└──────────────────────────────────────────────────────────────────────────────┘

    Railway Project
    ├── Frontend Service (React)
    │   ├── Root Directory: frontend/
    │   ├── Build Command: npm install && npm run build
    │   ├── Start Command: npx serve -s dist -l $PORT
    │   ├── Port: $PORT (Railway 자동 할당)
    │   └── Domain: your-app.railway.app
    │
    ├── Backend Service (FastAPI)
    │   ├── Root Directory: backend/
    │   ├── Build Command: pip install -r requirements.txt
    │   ├── Start Command: uvicorn src.main:app --host 0.0.0.0 --port $PORT
    │   ├── Port: $PORT (Railway 자동 할당)
    │   └── Domain: your-api.railway.app
    │
    ├── PostgreSQL (Railway 내장)
    │   └── Connection: DATABASE_URL (자동 생성)
    │
    └── Redis (Railway 내장)
        └── Connection: REDIS_URL (자동 생성)


┌──────────────────────────────────────────────────────────────────────────────┐
│                     Request/Response Flow                                     │
│                      (요청/응답 흐름)                                         │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                          1. 정적 리소스 로딩                             │
    └─────────────────────────────────────────────────────────────────────────┘

    Browser                       Railway (Frontend)
       │                                  │
       │  GET https://your-app.railway.app/
       │─────────────────────────────────▶│
       │                                  │
       │◀─────────────────────────────────│
       │    index.html + JS/CSS bundles   │
       │                                  │


    ┌─────────────────────────────────────────────────────────────────────────┐
    │                          2. API 요청 흐름                                │
    └─────────────────────────────────────────────────────────────────────────┘

    React App                    Railway API                  PostgreSQL
       │                             │                             │
       │  GET /api/v1/projects       │                             │
       │────────────────────────────▶│                             │
       │                             │  SELECT * FROM projects     │
       │                             │────────────────────────────▶│
       │                             │◀────────────────────────────│
       │◀────────────────────────────│  [{id, title, ...}]         │
       │  JSON Response              │                             │


    ┌─────────────────────────────────────────────────────────────────────────┐
    │                          3. 인증 흐름                                    │
    └─────────────────────────────────────────────────────────────────────────┘

    React App                    Railway API                     JWT
       │                             │                             │
       │  POST /auth/login           │                             │
       │  {email, password}          │                             │
       │────────────────────────────▶│                             │
       │                             │  검증 + JWT 생성            │
       │                             │────────────────────────────▶│
       │◀────────────────────────────│                             │
       │  Set-Cookie: access_token   │                             │
       │  Set-Cookie: refresh_token  │                             │
       │  (HTTPOnly, Secure)         │                             │
       │                             │                             │
       │  이후 요청들                 │                             │
       │  Cookie: access_token=...   │                             │
       │────────────────────────────▶│  토큰 검증                  │
       │                             │────────────────────────────▶│


    ┌─────────────────────────────────────────────────────────────────────────┐
    │                    4. 파일 업로드 + 태스크 생성                          │
    └─────────────────────────────────────────────────────────────────────────┘

    React App              Railway API           FileStorage        PostgreSQL
       │                        │                     │                  │
       │  POST /projects/:id/tasks                    │                  │
       │  Content-Type: multipart/form-data           │                  │
       │  [title, files[]]      │                     │                  │
       │───────────────────────▶│                     │                  │
       │                        │                     │                  │
       │                        │  1. Task 생성                          │
       │                        │────────────────────────────────────────▶
       │                        │                                        │
       │                        │  2. 파일 저장      │                  │
       │                        │───────────────────▶│                  │
       │                        │   storage/uploads/ │                  │
       │                        │   {user}/{task}/   │                  │
       │                        │◀───────────────────│                  │
       │                        │                     │                  │
       │                        │  3. 언어 감지 + 복잡도 분석            │
       │                        │                     │                  │
       │                        │  4. UploadedCode + CodeFile 저장       │
       │                        │────────────────────────────────────────▶
       │◀───────────────────────│                     │                  │
       │  TaskResponse          │                     │                  │


    ┌─────────────────────────────────────────────────────────────────────────┐
    │                    5. AI 문서 생성 흐름                                  │
    └─────────────────────────────────────────────────────────────────────────┘

    React App         Railway API        Celery Worker      Gemini API    PostgreSQL
       │                   │                   │                │              │
       │  POST /document/  │                   │                │              │
       │    generate       │                   │                │              │
       │──────────────────▶│                   │                │              │
       │                   │                   │                │              │
       │                   │  LearningDoc      │                │              │
       │                   │  (status: pending)│                │              │
       │                   │─────────────────────────────────────────────────▶│
       │                   │                   │                │              │
       │                   │  Celery Task 큐   │                │              │
       │                   │──────────────────▶│                │              │
       │◀──────────────────│                   │                │              │
       │  202 Accepted     │                   │                │              │
       │                   │                   │                │              │
       │                   │                   │  status:       │              │
       │                   │                   │  in_progress   │              │
       │                   │                   │────────────────────────────▶ │
       │                   │                   │                │              │
       │                   │                   │  프롬프트 생성 │              │
       │                   │                   │───────────────▶│              │
       │                   │                   │                │              │
       │                   │                   │◀───────────────│              │
       │                   │                   │  JSON (7장)    │              │
       │                   │                   │                │              │
       │                   │                   │  status:       │              │
       │                   │                   │  completed     │              │
       │                   │                   │  content: {...}│              │
       │                   │                   │────────────────────────────▶ │
       │                   │                   │                │              │
       │   Polling (3초)   │                   │                │              │
       │──────────────────▶│                   │                │              │
       │  GET /document    │                   │                │              │
       │                   │◀────────────────────────────────────────────────│
       │◀──────────────────│                   │                │              │
       │  Document         │                   │                │              │
       │  (7 Chapters)     │                   │                │              │


┌──────────────────────────────────────────────────────────────────────────────┐
│                         Data Transformation                                   │
│                      (데이터 변환 흐름)                                       │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                      Frontend (TypeScript)                               │
    │                         camelCase                                        │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                          │
    │   interface Task {                                                       │
    │     id: string;                                                          │
    │     projectId: string;          ← 변환됨                                 │
    │     taskNumber: number;         ← 변환됨                                 │
    │     title: string;                                                       │
    │     description?: string;                                                │
    │     uploadMethod: 'file' | 'folder' | 'paste';   ← 변환됨               │
    │     uploadedCode?: UploadedCode;  ← 변환됨                               │
    │     createdAt: string;          ← 변환됨                                 │
    │     updatedAt: string;          ← 변환됨                                 │
    │   }                                                                      │
    │                                                                          │
    └────────────────────────────────────────┬────────────────────────────────┘
                                             │
                            Service Layer 변환 함수
                            transformTask(dto) → Task
                                             │
                                             ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                         API Response                                     │
    │                         JSON (HTTP)                                      │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                          │
    │   {                                                                      │
    │     "id": "uuid-string",                                                 │
    │     "project_id": "uuid-string",         ← snake_case                   │
    │     "task_number": 1,                    ← snake_case                   │
    │     "title": "My Task",                                                  │
    │     "description": null,                                                 │
    │     "upload_method": "file",             ← snake_case                   │
    │     "uploaded_code": {...},              ← snake_case                   │
    │     "created_at": "2025-01-01T...",      ← snake_case                   │
    │     "updated_at": "2025-01-01T..."       ← snake_case                   │
    │   }                                                                      │
    │                                                                          │
    └────────────────────────────────────────┬────────────────────────────────┘
                                             │
                                             │
                                             ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                        Backend (Python)                                  │
    │                         snake_case                                       │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                          │
    │   class Task(Base):                                                      │
    │       __tablename__ = "tasks"                                            │
    │                                                                          │
    │       id: Mapped[UUID]                                                   │
    │       project_id: Mapped[UUID]           ← snake_case                   │
    │       task_number: Mapped[int]           ← snake_case                   │
    │       title: Mapped[str]                                                 │
    │       description: Mapped[Optional[str]]                                 │
    │       upload_method: Mapped[str]         ← snake_case                   │
    │       created_at: Mapped[datetime]       ← snake_case                   │
    │       updated_at: Mapped[datetime]       ← snake_case                   │
    │                                                                          │
    └─────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                           CORS Configuration                                  │
│                          (교차 출처 설정)                                     │
└──────────────────────────────────────────────────────────────────────────────┘

    Backend (main.py):
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                                                                          │
    │   # Railway 통합 배포 시 동일 도메인이면 CORS 불필요                     │
    │   # 별도 서비스 배포 시 아래 설정 사용                                   │
    │                                                                          │
    │   app.add_middleware(                                                    │
    │       CORSMiddleware,                                                    │
    │       allow_origins=[                                                    │
    │           "https://your-app.railway.app",    # Frontend                  │
    │           "http://localhost:5173",           # Development               │
    │       ],                                                                 │
    │       allow_credentials=True,  # 쿠키 허용 (JWT)                         │
    │       allow_methods=["*"],                                               │
    │       allow_headers=["*"],                                               │
    │   )                                                                      │
    │                                                                          │
    └─────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                      Environment Variables                                    │
│                         (환경 변수 설정)                                      │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                     Railway (Frontend)                                   │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                          │
    │   VITE_API_BASE_URL=https://your-api.railway.app/api/v1                 │
    │                                                                          │
    └─────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                      Railway (Backend)                                   │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                          │
    │   # Database (PostgreSQL - Railway 내장)                                 │
    │   DATABASE_URL=postgresql://postgres:***@db.railway.internal:5432/db    │
    │                                                                          │
    │   # Redis (Railway 내장)                                                 │
    │   REDIS_URL=redis://default:***@redis.railway.internal:6379             │
    │   CELERY_BROKER_URL=redis://redis.railway.internal:6379/1               │
    │   CELERY_RESULT_BACKEND=redis://redis.railway.internal:6379/2           │
    │                                                                          │
    │   # Application                                                          │
    │   APP_ENV=production                                                     │
    │   SECRET_KEY=your-super-secret-key-here                                  │
    │   CORS_ORIGINS=https://your-app.railway.app                              │
    │                                                                          │
    │   # AI                                                                   │
    │   GEMINI_API_KEY=your-gemini-api-key                                     │
    │   GEMINI_MODEL=gemini-pro                                                │
    │                                                                          │
    │   # JWT                                                                  │
    │   JWT_SECRET_KEY=your-jwt-secret                                         │
    │   ACCESS_TOKEN_EXPIRE_MINUTES=15                                         │
    │   REFRESH_TOKEN_EXPIRE_DAYS=7                                            │
    │                                                                          │
    └─────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                        GitHub Auto Deploy                                     │
│                      (GitHub 자동 배포 흐름)                                  │
└──────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │    Developer    │
                              │   git push      │
                              └────────┬────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │     GitHub      │
                              │   Repository    │
                              │   (monorepo)    │
                              └────────┬────────┘
                                       │
                                       │ Webhook Trigger
                                       ▼
                              ┌─────────────────┐
                              │     Railway     │
                              │    Platform     │
                              └────────┬────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
           ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
           │   Frontend    │  │    Backend    │  │   Databases   │
           │   Service     │  │    Service    │  │               │
           │               │  │               │  │  PostgreSQL   │
           │ Root: frontend│  │ Root: backend │  │     Redis     │
           │               │  │               │  │               │
           │ 1. npm install│  │ 1. pip install│  │  (자동 연결)  │
           │ 2. npm build  │  │ 2. uvicorn    │  │               │
           │ 3. serve dist │  │    start      │  │               │
           │               │  │               │  │               │
           │ ~1-2분        │  │ ~1-2분        │  │               │
           └───────────────┘  └───────────────┘  └───────────────┘
                    │                  │
                    ▼                  ▼
           ┌───────────────┐  ┌───────────────┐
           │ your-app.     │  │ your-api.     │
           │ railway.app   │  │ railway.app   │
           └───────────────┘  └───────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                            Cost Summary                                       │
│                           (비용 요약)                                         │
└──────────────────────────────────────────────────────────────────────────────┘

    ┌───────────────────────────────────────────────────────────────────┐
    │                                                                    │
    │   Railway (전체 인프라)                                            │
    │   ├─ Hobby Plan: $5/월 구독                                        │
    │   ├─ 포함 크레딧: $5/월                                            │
    │   ├─ 예상 사용량:                                                  │
    │   │   ├─ Frontend (Static): ~$0.5-1                                │
    │   │   ├─ Backend API: ~$2-3                                        │
    │   │   ├─ Celery Worker: ~$1-2                                      │
    │   │   ├─ PostgreSQL: ~$1-2                                         │
    │   │   └─ Redis: ~$0.5-1                                            │
    │   └─ 예상 비용: $5-8/월                                            │
    │                                                                    │
    │   Gemini API                                                       │
    │   ├─ Free Tier: 분당 60 요청                                       │
    │   └─ 비용: $0/월 (무료 한도 내)                                    │
    │                                                                    │
    │   ═══════════════════════════════════════════════════════════════  │
    │   총 예상 비용: $5-8/월                                            │
    │   첫 달: $0 (Railway Trial $5 크레딧)                              │
    │                                                                    │
    │   장점:                                                            │
    │   • 단일 플랫폼 관리 (간편)                                        │
    │   • 내부 네트워크 통신 (빠름)                                      │
    │   • 자동 SSL 인증서                                                │
    │   • GitHub 연동 자동 배포                                          │
    │                                                                    │
    └───────────────────────────────────────────────────────────────────┘
```
