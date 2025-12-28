# Backend Architecture

AI Code Learning Platform - FastAPI 기반 백엔드 서버 내부 구조

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                           BACKEND ARCHITECTURE                                ║
║                         AI Code Learning Platform                             ║
╚══════════════════════════════════════════════════════════════════════════════╝


┌──────────────────────────────────────────────────────────────────────────────┐
│                              main.py                                          │
│                        ┌──────────────────┐                                   │
│                        │     FastAPI      │                                   │
│                        │   Application    │                                   │
│                        │                  │                                   │
│                        │ • CORS 설정      │                                   │
│                        │ • 라우터 등록    │                                   │
│                        │ • DB 초기화      │                                   │
│                        └────────┬─────────┘                                   │
└─────────────────────────────────┼─────────────────────────────────────────────┘
                                  │
                                  │ /api/v1 라우팅 등록
                                  │
        ┌─────────────────────────┼─────────────────────────┬───────────────────┐
        │                         │                         │                   │
        ▼                         ▼                         ▼                   ▼
┌───────────────┐     ┌───────────────────┐     ┌───────────────┐     ┌─────────────────┐
│  auth.py      │     │   projects.py     │     │   tasks.py    │     │  documents.py   │
│  /auth        │     │   /projects       │     │   /tasks      │     │  /tasks/.../    │
│               │     │                   │     │               │     │   document      │
├───────────────┤     ├───────────────────┤     ├───────────────┤     ├─────────────────┤
│POST /register │     │GET    /           │     │GET  /{id}     │     │GET    /         │
│POST /login    │     │POST   /           │     │PATCH/{id}     │     │POST   /generate │
│POST /logout   │     │GET    /{id}       │     │DELETE/{id}    │     │GET    /status   │
│POST /refresh  │     │PATCH  /{id}       │     │GET  /{id}/code│     │                 │
│GET  /me       │     │DELETE /{id}       │     │               │     │                 │
│               │     │POST   /{id}/restore│    │[프로젝트 하위]│     │                 │
│               │     │DELETE /{id}/perm  │     │GET  /         │     │                 │
│               │     │                   │     │POST /         │     │                 │
└───────┬───────┘     └─────────┬─────────┘     └───────┬───────┘     └────────┬────────┘
        │                       │                       │                      │
        │                       │                       │                      │
        └───────────────────────┴───────────────────────┴──────────────────────┘
                                          │
                                          │ 의존성 주입 (Depends)
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          dependencies.py                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  의존성 함수:                                                                 │
│  ┌────────────────────────┐  ┌────────────────────────┐                      │
│  │ get_session()          │  │ get_current_user()     │                      │
│  │ → AsyncSession         │  │ → User                 │                      │
│  │                        │  │                        │                      │
│  │ DB 세션 생성/해제      │  │ JWT 쿠키 검증          │                      │
│  │ 트랜잭션 관리          │  │ 사용자 정보 조회       │                      │
│  └────────────────────────┘  └────────────────────────┘                      │
│                                                                               │
│  ┌────────────────────────┐  ┌────────────────────────┐                      │
│  │ get_storage_service()  │  │ verify_access_token()  │                      │
│  │ → FileStorageService   │  │ → user_id (UUID)       │                      │
│  │                        │  │                        │                      │
│  │ 파일 저장소 인스턴스   │  │ 토큰 디코딩/검증       │                      │
│  └────────────────────────┘  └────────────────────────┘                      │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                         Schema/Validation Layer                               │
│                              (Pydantic)                                       │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Auth Schemas   │   │ Project Schemas │   │  Task Schemas   │   │Document Schemas │
├─────────────────┤   ├─────────────────┤   ├─────────────────┤   ├─────────────────┤
│                 │   │                 │   │                 │   │                 │
│• RegisterReq    │   │• ProjectCreate  │   │• TaskCreate     │   │• DocumentResp   │
│  - email: str   │   │  - title: str   │   │  - title: str   │   │  - id: UUID     │
│  - password:str │   │  - description? │   │  - description? │   │  - status: str  │
│                 │   │                 │   │  - upload_type  │   │  - chapters:{}  │
│• LoginReq       │   │• ProjectUpdate  │   │                 │   │                 │
│  - email: str   │   │  - title?       │   │• TaskResponse   │   │• GenerateResp   │
│  - password:str │   │  - description? │   │  - id: UUID     │   │  - task_id:UUID │
│                 │   │                 │   │  - task_number  │   │  - status: str  │
│• TokenResp      │   │• ProjectResp    │   │  - title: str   │   │  - message: str │
│  - user: User   │   │  - id: UUID     │   │  - project_id   │   │                 │
│  - message: str │   │  - title: str   │   │  - uploaded_code│   │• StatusResp     │
│                 │   │  - created_at   │   │  - created_at   │   │  - status: str  │
│검증:            │   │                 │   │                 │   │  - progress: %  │
│• 이메일 형식    │   │검증:            │   │검증:            │   │  - error?: str  │
│• 비밀번호 8자+  │   │• title 1자 이상 │   │• title 5자 이상 │   │                 │
│                 │   │                 │   │• desc 500자 이하│   │                 │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │                     │
         │                     │ 사용                │                     │
         ▼                     ▼                     ▼                     ▼


┌──────────────────────────────────────────────────────────────────────────────┐
│                            Service Layer                                      │
│                         (비즈니스 로직 처리)                                  │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│    AuthService      │   │   ProjectService    │   │    TaskService      │
│  (user_service.py)  │   │ (project_service.py)│   │  (task_service.py)  │
├─────────────────────┤   ├─────────────────────┤   ├─────────────────────┤
│                     │   │                     │   │                     │
│• register()         │   │• create()           │   │• create()           │
│  └─ 이메일 중복검증 │   │  └─ Project 인스턴스│   │  └─ task_number 계산│
│  └─ bcrypt 해싱     │   │     생성            │   │  └─ Task 인스턴스   │
│  └─ User 저장       │   │                     │   │     생성            │
│                     │   │• get_by_id()        │   │                     │
│• authenticate()     │   │  └─ 소유권 검증     │   │• get_by_id()        │
│  └─ User 조회       │   │  └─ 404 처리        │   │  └─ 소유권 검증     │
│  └─ 비밀번호 검증   │   │                     │   │  └─ eager loading   │
│                     │   │• get_by_user()      │   │                     │
│                     │   │  └─ active만 필터링 │   │• get_by_project()   │
└─────────┬───────────┘   │  └─ 정렬 적용       │   │  └─ task_number 정렬│
          │               │                     │   │                     │
          │               │• update()           │   │• update()           │
          │               │  └─ 소유권 확인     │   │  └─ 소유권 확인     │
          │               │  └─ 필드 업데이트   │   │                     │
          │               │                     │   │• soft_delete()      │
          │               │• soft_delete()      │   │  └─ trashed 상태    │
          │               │  └─ deletion_status │   │  └─ 30일 후 삭제    │
          │               │     = 'trashed'     │   │                     │
          │               │  └─ 30일 보관       │   │• get_by_id_with_    │
          │               │                     │   │  code()             │
          │               │• restore()          │   │  └─ UploadedCode    │
          │               │  └─ active로 복원   │   │  └─ CodeFiles       │
          │               │                     │   │     함께 로드       │
          │               │• permanent_delete() │   │                     │
          │               │  └─ 영구 삭제       │   │                     │
          │               │                     │   │                     │
          ▼               └──────────┬──────────┘   └──────────┬──────────┘
                                     │                         │
┌─────────────────────┐              │                         │
│   TokenService      │              │                         │
│ (token_service.py)  │              │                         │
├─────────────────────┤              │                         │
│                     │              │                         │
│• create_access_     │              │                         │
│  token()            │              │                         │
│  └─ 15분 유효       │              │                         │
│  └─ HS256 서명      │              │                         │
│                     │              │                         │
│• create_refresh_    │              │                         │
│  token()            │              │                         │
│  └─ 7일 유효        │              │                         │
│  └─ DB 저장         │              │                         │
│                     │              │                         │
│• rotate_refresh_    │              │                         │
│  token()            │              │                         │
│  └─ 기존 토큰 삭제  │              │                         │
│  └─ 새 토큰 발급    │              │                         │
│                     │              │                         │
│• revoke_token()     │              │                         │
│  └─ 로그아웃 처리   │              │                         │
└─────────────────────┘              │                         │
                                     │                         │
                                     │                         │
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Code Analysis Services                                │
│                       (code_analysis/ 폴더)                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│ CodeUploadService   │   │  LanguageDetector   │   │ ComplexityAnalyzer  │
├─────────────────────┤   ├─────────────────────┤   ├─────────────────────┤
│                     │   │                     │   │                     │
│• upload_files()     │──▶│• detect_language()  │   │• analyze()          │
│  └─ 파일 저장       │   │  └─ 확장자 기반     │   │  └─ 라인 수 분석    │
│  └─ 언어 감지       │   │  └─ 내용 분석       │   │  └─ 복잡도 계산     │
│  └─ 복잡도 분석     │──▶│  └─ 매핑 테이블     │──▶│  └─ beginner/       │
│  └─ UploadedCode    │   │                     │   │     intermediate/   │
│     생성            │   │Supported:           │   │     advanced        │
│  └─ CodeFile[]      │   │• .py  → Python      │   │                     │
│     생성            │   │• .js  → JavaScript  │   │기준:                │
│                     │   │• .ts  → TypeScript  │   │• 총 라인 수         │
│• upload_paste()     │   │• .jsx → React       │   │• 중첩 깊이          │
│  └─ 붙여넣기 처리   │   │• .tsx → React TS    │   │• 함수/클래스 수     │
│  └─ 임시 파일 생성  │   │• .java→ Java        │   │                     │
└─────────┬───────────┘   │• .cpp → C++         │   └─────────────────────┘
          │               │• .c   → C           │
          │               │• .html→ HTML        │
          ▼               │• .css → CSS         │
                          └─────────────────────┘
┌─────────────────────┐
│ FileStorageService  │
├─────────────────────┤
│                     │
│• save_files()       │
│  └─ 저장 경로 생성  │
│  storage/uploads/   │
│   └─{user_id}/      │
│     └─{task_id}/    │
│       └─{uuid}.ext  │
│                     │
│• read_file()        │
│  └─ 파일 내용 읽기  │
│                     │
│• delete_files()     │
│  └─ 파일 삭제       │
└─────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                      Document Generation Services                            │
│                           (document/ 폴더)                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐        ┌──────────────────────────┐
│ DocumentGenerationService│        │      GeminiClient        │
│                          │        │     (ai/gemini_client.py)│
├──────────────────────────┤        ├──────────────────────────┤
│                          │        │                          │
│• generate_document()     │        │• generate()              │
│  └─ LearningDoc 생성     │───────▶│  └─ API 호출             │
│     (pending 상태)       │        │  └─ 재시도 로직          │
│  └─ 프롬프트 빌드        │        │     (최대 3회)           │
│  └─ AI 호출              │        │  └─ 지수 백오프          │
│  └─ 응답 파싱/검증       │        │                          │
│  └─ 7장 구조 확인        │        │Rate Limit 처리:          │
│  └─ DB 저장              │        │• 429 에러 감지           │
│     (completed 상태)     │        │• 3^attempt 초 대기       │
│                          │        │                          │
│• get_document()          │        │Timeout 처리:             │
│  └─ task_id로 조회       │        │• 30초 타임아웃           │
│                          │        │• 2^attempt 초 대기       │
│• get_status()            │        │                          │
│  └─ 생성 상태 반환       │        └──────────────────────────┘
│                          │                    │
│                          │                    │ 호출
│검증 (REQUIRED_CHAPTERS): │                    ▼
│• chapter1 (요약)         │        ┌──────────────────────────┐
│• chapter2 (사전지식)     │        │     PromptBuilder        │
│• chapter3 (핵심로직)     │        ├──────────────────────────┤
│• chapter4 (라인별설명)   │        │                          │
│• chapter5 (문법참조)     │        │• get_system_instruction()│
│• chapter6 (패턴)         │        │  └─ AI 역할 정의         │
│• chapter7 (연습문제)     │        │  └─ 출력 형식 지정       │
│                          │        │                          │
└──────────────────────────┘        │• build_document_prompt() │
                                    │  └─ 코드 내용 포함       │
                                    │  └─ 사용자 레벨 반영     │
                                    │  └─ 7장 구조 요청        │
                                    │                          │
                                    └──────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────┐
│                            ORM/Model Layer                                    │
│                           (SQLAlchemy Models)                                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐        ┌─────────────────────┐        ┌─────────────────────┐
│     User Model      │        │   Project Model     │        │    Task Model       │
│    (user.py)        │        │   (project.py)      │        │    (task.py)        │
├─────────────────────┤        ├─────────────────────┤        ├─────────────────────┤
│ Table: users        │        │ Table: projects     │        │ Table: tasks        │
│                     │        │                     │        │                     │
│• id: UUID (PK)      │◄───────┤• user_id: UUID (FK) │◄───────┤• project_id:        │
│• email: str         │   1:N  │                     │   1:N  │  UUID (FK)          │
│  (UNIQUE)           │        │• id: UUID (PK)      │        │                     │
│• password_hash: str │        │• title: str         │        │• id: UUID (PK)      │
│• skill_level: str   │        │  (min 1 char)       │        │• task_number: int   │
│  (default:          │        │• description: text  │        │  (unique per proj)  │
│   "Complete         │        │                     │        │• title: str         │
│    Beginner")       │        │• deletion_status:   │        │  (min 5 chars)      │
│• created_at         │        │  'active'|'trashed' │        │• description: text  │
│• updated_at         │        │• trashed_at         │        │  (max 500 chars)    │
│• last_login_at      │        │• scheduled_deletion_│        │• upload_method:     │
│                     │        │  at                 │        │  'file'|'folder'|   │
│Relationships:       │        │• created_at         │        │  'paste'            │
│• projects: List     │────────┤• updated_at         │        │• deletion_status    │
│                     │        │• last_activity_at   │        │• created_at         │
│Index:               │        │                     │        │• updated_at         │
│• idx_users_email    │        │Relationships:       │        │                     │
│                     │        │• user: User         │        │Relationships:       │
└─────────────────────┘        │• tasks: List[Task]  │────────┤• project: Project   │
                               │                     │        │• uploaded_code: 1:1 │
                               │Indexes:             │        │• learning_doc: 1:1  │
                               │• idx_projects_      │        │                     │
                               │  user_id            │        │Indexes:             │
                               │• idx_projects_      │        │• idx_tasks_         │
                               │  deletion_status    │        │  project_id         │
                               │                     │        │• idx_tasks_         │
                               └─────────────────────┘        │  deletion_status    │
                                                              │• idx_tasks_         │
                                                              │  number_order       │
                                                              │                     │
                                                              └──────────┬──────────┘
                                                                         │
                                            ┌────────────────────────────┼────────────────────────────┐
                                            │                            │                            │
                                            ▼                            │                            ▼
                               ┌─────────────────────┐                   │               ┌─────────────────────┐
                               │  UploadedCode Model │                   │               │LearningDocument     │
                               │ (uploaded_code.py)  │                   │               │    Model            │
                               ├─────────────────────┤                   │               ├─────────────────────┤
                               │ Table:              │                   │               │ Table:              │
                               │  uploaded_codes     │                   │               │ learning_documents  │
                               │                     │                   │               │                     │
                               │• id: UUID (PK)      │                   │               │• id: UUID (PK)      │
                               │• task_id: UUID (FK) │◄──────────────────┼──────────────▶│• task_id: UUID (FK) │
                               │  (UNIQUE - 1:1)     │                1:1│               │  (UNIQUE - 1:1)     │
                               │• detected_language  │                   │               │• content: JSONB     │
                               │• complexity_level:  │                   │               │  (7 Chapters)       │
                               │  'beginner'|        │                   │               │• generation_status: │
                               │  'intermediate'|    │                   │               │  'pending'|         │
                               │  'advanced'         │                   │               │  'in_progress'|     │
                               │• total_lines: int   │                   │               │  'completed'|       │
                               │• total_files: int   │                   │               │  'failed'           │
                               │• upload_size_bytes  │                   │               │• generation_error   │
                               │  (max 10MB)         │                   │               │• celery_task_id     │
                               │• created_at         │                   │               │• created_at         │
                               │                     │                   │               │• updated_at         │
                               │Relationships:       │                   │               │• generation_        │
                               │• task: Task         │                   │               │  started_at         │
                               │• code_files: List   │                   │               │• generation_        │
                               │                     │                   │               │  completed_at       │
                               └──────────┬──────────┘                   │               │                     │
                                          │                              │               │Relationship:        │
                                          │ 1:N                          │               │• task: Task         │
                                          ▼                              │               │                     │
                               ┌─────────────────────┐                   │               └─────────────────────┘
                               │   CodeFile Model    │                   │
                               │   (code_file.py)    │                   │
                               ├─────────────────────┤                   │
                               │ Table: code_files   │                   │
                               │                     │                   │
                               │• id: UUID (PK)      │                   │
                               │• uploaded_code_id   │                   │
                               │  (FK)               │                   │
                               │• file_name: str     │                   │
                               │• file_path: str     │                   │
                               │  (relative)         │                   │
                               │• file_extension     │                   │
                               │• file_size_bytes    │                   │
                               │• storage_path       │                   │
                               │  (absolute)         │                   │
                               │• mime_type          │                   │
                               │• created_at         │                   │
                               │                     │                   │
                               │Relationship:        │                   │
                               │• uploaded_code      │                   │
                               │                     │                   │
                               │Supported extensions:│                   │
                               │ .py .js .ts .jsx    │                   │
                               │ .tsx .html .css     │                   │
                               │ .java .cpp .c       │                   │
                               │ .txt .md            │                   │
                               └─────────────────────┘                   │
                                          │                              │
                                          │ SQL 실행                     │
                                          ▼                              │
                                                                         │
┌────────────────────────────────────────────────────────────────────────┼───────┐
│                         Database Layer                                 │       │
│                        (db/ 폴더)                                      │       │
└────────────────────────────────────────────────────────────────────────┼───────┘
                                                                         │
┌─────────────────────────────┐        ┌─────────────────────────────────▼───────┐
│       config.py             │        │              session.py                 │
├─────────────────────────────┤        ├─────────────────────────────────────────┤
│                             │        │                                         │
│ DatabaseConfig:             │        │ get_session():                          │
│ • 환경변수에서 설정 로드    │───────▶│   AsyncGenerator[AsyncSession]          │
│                             │        │                                         │
│ 우선순위:                   │        │ • create_async_engine()                 │
│ 1. DATABASE_URL             │        │ • async_sessionmaker()                  │
│ 2. 개별 설정:               │        │ • yield session                         │
│    - DB_HOST/POSTGRES_HOST  │        │ • session.close()                       │
│    - DB_PORT (기본: 5432)   │        │                                         │
│    - DB_NAME/POSTGRES_DB    │        │ 연결 풀 설정:                           │
│    - DB_USER/POSTGRES_USER  │        │ • pool_size: 10                         │
│    - DB_PASSWORD            │        │ • max_overflow: 20                      │
│                             │        │ • pool_timeout: 30                      │
│ URL 자동 변환:              │        │ • pool_recycle: 3600                    │
│ postgresql:// →             │        │ • pool_pre_ping: True                   │
│ postgresql+asyncpg://       │        │                                         │
│                             │        │ init_db():                              │
│ 특수문자 처리:              │        │ • Base.metadata.create_all()            │
│ quote_plus(password)        │        │ • 테이블 자동 생성                      │
│                             │        │                                         │
└─────────────────────────────┘        └─────────────────────────────────────────┘
                                                         │
                                                         │ 연결
                                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PostgreSQL Database                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Tables:                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   users     │  │  projects   │  │   tasks     │  │    uploaded_codes       │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│  ┌─────────────┐  ┌───────────────────────┐  ┌────────────────────────────────┐ │
│  │ code_files  │  │  learning_documents   │  │       refresh_tokens           │ │
│  └─────────────┘  └───────────────────────┘  └────────────────────────────────┘ │
│                                                                                  │
│  Indexes:                          Constraints:                                  │
│  • users.email (unique)            • Foreign Keys (CASCADE)                      │
│  • projects.user_id                • CHECK (title_min_length)                    │
│  • projects.deletion_status        • CHECK (valid_deletion_status)               │
│  • tasks.project_id                • CHECK (upload_size_bytes <= 10MB)           │
│  • tasks.(project_id, task_number) • UNIQUE (task_number per project)            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Celery Task Queue (Optional)                            │
│                              (tasks/ 폴더)                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                              celery_app.py                                        │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  Celery App: "codelearn"                                                          │
│                                                                                   │
│  Config (CeleryConfig):                                                           │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │ • broker_url: redis://localhost:6379/1 (CELERY_BROKER_URL)                 │  │
│  │ • result_backend: redis://localhost:6379/2 (CELERY_RESULT_BACKEND)         │  │
│  │ • task_time_limit: 600초 (10분)                                            │  │
│  │ • task_soft_time_limit: 540초 (9분) - cleanup 여유                         │  │
│  │ • worker_prefetch_multiplier: 1 (AI 장시간 작업)                           │  │
│  │ • task_acks_late: True (완료 후 승인)                                      │  │
│  │ • task_reject_on_worker_lost: True (worker 다운 시 재시도)                 │  │
│  │ • accept_content: ["json"] (pickle 제외 - 보안)                            │  │
│  │ • task_track_started: True (시작 상태 추적)                                │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                   │
│  Tasks:                                                                           │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │ @app.task                                                                  │  │
│  │ def generate_learning_document(task_id: str) -> dict:                      │  │
│  │     """비동기 AI 문서 생성 태스크"""                                       │  │
│  │     - DocumentGenerationService 호출                                       │  │
│  │     - 상태 업데이트 (pending → in_progress → completed/failed)             │  │
│  │     - 에러 처리 및 재시도                                                  │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                   │
└────────────────────────────────────────────────────┬──────────────────────────────┘
                                                     │
                                                     │ 메시지 전송
                                                     ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                               Redis                                               │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────────┐        ┌─────────────────────────┐                  │
│  │   DB 1: Task Broker     │        │  DB 2: Result Backend   │                  │
│  │                         │        │                         │                  │
│  │ • 작업 큐 저장          │        │ • 작업 결과 저장        │                  │
│  │ • Worker가 가져감       │        │ • 상태 조회용           │                  │
│  └─────────────────────────┘        └─────────────────────────┘                  │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Request Flow Summary                                │
│                            (요청 처리 흐름 요약)                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

    HTTP Request
         │
         ▼
    ┌─────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
    │ FastAPI │────▶│ Dependencies │────▶│   Service   │────▶│  Model   │
    │ Router  │     │ (인증/세션)  │     │(비즈니스)   │     │  (ORM)   │
    └─────────┘     └──────────────┘     └─────────────┘     └──────────┘
         │                                      │                  │
         │                                      │                  │
         ▼                                      ▼                  ▼
    ┌─────────┐                          ┌──────────┐       ┌──────────┐
    │ Schema  │                          │ External │       │PostgreSQL│
    │(검증)   │                          │  APIs    │       │          │
    └─────────┘                          │(Gemini)  │       │          │
                                         └──────────┘       └──────────┘
```
