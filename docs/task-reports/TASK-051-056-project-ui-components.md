# Task Report: T051-T056 Project UI Components

## 개요

| 항목 | 내용 |
|------|------|
| Task ID | T051, T052, T053, T054, T055, T056 |
| 제목 | Project UI Components |
| 상태 | 완료 |
| 개발 방법 | TDD (Component-First Development) |

## 구현된 기능

### T051: ProjectCard 컴포넌트
- 프로젝트 정보를 카드 형태로 표시
- 제목, 설명, 생성일, 최종 활동일 표시
- 프로젝트 상세 페이지로 이동 링크

### T052: CreateProjectModal 컴포넌트
- 새 프로젝트 생성을 위한 모달 다이얼로그
- 제목(필수), 설명(선택) 입력 폼
- 로딩 상태 및 에러 처리

### T053: project-service
- 프로젝트 CRUD API 호출 서비스
- snake_case → camelCase 변환
- API 클라이언트 통합

### T054: Dashboard 페이지 구현
- 프로젝트 목록 표시 (그리드 레이아웃)
- 빈 상태, 로딩 상태, 에러 상태 처리
- 새 프로젝트 생성 버튼 및 모달 연동
- TanStack Query를 통한 데이터 페칭

### T055: ProjectDetail 페이지 구현
- 프로젝트 상세 정보 표시
- 통계 카드 (생성일, 최종 활동, 작업 수)
- 뒤로가기 네비게이션

### T056: 프로젝트 삭제 플로우
- AlertDialog를 통한 삭제 확인
- 소프트 삭제 후 대시보드로 리다이렉트
- TanStack Query 캐시 무효화

## 파일 변경 내역

### 신규 파일
| 파일 | 설명 |
|------|------|
| `frontend/src/services/project-service.ts` | 프로젝트 CRUD API 서비스 |
| `frontend/src/components/project/ProjectCard.tsx` | 프로젝트 카드 컴포넌트 |
| `frontend/src/components/project/CreateProjectModal.tsx` | 프로젝트 생성 모달 |
| `frontend/src/components/ui/alert-dialog.tsx` | AlertDialog UI 컴포넌트 |
| `frontend/index.html` | Vite 진입점 HTML |
| `frontend/tsconfig.json` | TypeScript 루트 설정 |

### 수정된 파일
| 파일 | 변경 내용 |
|------|-----------|
| `frontend/src/pages/Dashboard.tsx` | 프로젝트 목록 및 생성 기능 구현 |
| `frontend/src/pages/ProjectDetail.tsx` | 프로젝트 상세 및 삭제 기능 구현 |
| `frontend/tsconfig.app.json` | 테스트 파일 exclude 추가 |

## 주요 컴포넌트

### project-service.ts
```typescript
export interface Project {
  id: string
  title: string
  description: string | null
  createdAt: string
  updatedAt: string
  lastActivityAt: string
  deletionStatus: string
  trashedAt: string | null
}

export const projectService = {
  getProjects(includeTrashed?: boolean): Promise<ProjectListResponse>
  getProject(id: string): Promise<Project>
  createProject(title: string, description?: string): Promise<Project>
  updateProject(id: string, data: UpdateProjectData): Promise<Project>
  deleteProject(id: string): Promise<void>
}
```

### ProjectCard 컴포넌트
- Props: `project: Project`
- 기능: 프로젝트 정보 표시, 클릭 시 상세 페이지 이동
- UI: Card 컴포넌트 기반, 한국어 날짜 포맷

### CreateProjectModal 컴포넌트
- Props: `open`, `onOpenChange`, `onSubmit`
- 기능: 프로젝트 생성 폼, 유효성 검사, 로딩/에러 상태
- UI: Dialog 컴포넌트 기반

### Dashboard 페이지
- 상태 관리: TanStack Query (`useQuery`, `useMutation`)
- 기능: 프로젝트 목록 조회, 새 프로젝트 생성
- UI: 그리드 레이아웃, 빈 상태/로딩/에러 처리

### ProjectDetail 페이지
- 상태 관리: TanStack Query, React Router
- 기능: 프로젝트 상세 조회, 삭제 (AlertDialog 확인)
- UI: 헤더, 통계 카드, 삭제 버튼

## 의존성

### 추가된 패키지
- `@radix-ui/react-alert-dialog`: AlertDialog 컴포넌트

### 기존 의존성
- React 18
- TanStack Query v5
- React Router v6
- shadcn/ui (Card, Dialog, Button, Input, Textarea)
- Tailwind CSS

## UI/UX 특징

### 한국어 지원
- 모든 UI 텍스트 한국어
- 날짜 포맷: `ko-KR` 로케일 사용

### 상태 처리
| 상태 | 표시 내용 |
|------|-----------|
| 로딩 중 | "프로젝트 목록을 불러오는 중..." |
| 에러 | "프로젝트 목록을 불러오는데 실패했습니다." |
| 빈 목록 | "아직 프로젝트가 없습니다." + 생성 버튼 |

### 반응형 디자인
- 그리드: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`
- 모달: `sm:max-w-[425px]`

## 빌드 결과

```
vite v6.3.5 building for production...
✓ 1386 modules transformed.
dist/index.html                   0.46 kB │ gzip:  0.29 kB
dist/assets/index-DjQa4Dv2.css   23.00 kB │ gzip:  5.02 kB
dist/assets/index-C2xNHRD_.js   293.12 kB │ gzip: 95.61 kB
✓ built in 3.05s
```

## 에러 처리

| 에러 상황 | 처리 방법 |
|----------|----------|
| API 호출 실패 | TanStack Query 에러 상태로 UI 표시 |
| 프로젝트 생성 실패 | 모달 내 에러 메시지 표시 |
| 프로젝트 삭제 실패 | 콘솔 에러 로깅 |
| 인증 만료 | API 클라이언트에서 자동 처리 |
