# Task 018: React Router 설정

**작업 완료일**: 2025-11-20
**관련 이슈**: Phase 2 - Frontend Foundation
**TDD 사이클**: RED → GREEN

---

## 무엇을 만들었나요?

웹 애플리케이션의 페이지 이동을 관리하는 React Router를 설정했습니다. 사용자가 다양한 페이지(로그인, 대시보드, 프로젝트 상세, 태스크 상세 등) 사이를 자유롭게 이동할 수 있게 하는 길을 만들었습니다.

도서관을 생각해보세요. 책 검색대, 열람실, 대출 데스크, 참고 자료실 등 각각의 공간이 있고, 각 공간마다 번호가 붙은 안내 표지판이 있죠. React Router는 이런 표지판과 길을 만드는 역할입니다. 사용자가 "/login" 주소를 입력하면 로그인 페이지로, "/dashboard"를 입력하면 대시보드로 안내합니다.

---

## 왜 이렇게 만들었나요?

우리 플랫폼은 여러 기능이 있습니다:
- 사용자 등록/로그인
- 프로젝트 목록 보기
- 각 프로젝트의 태스크 관리
- 태스크별 학습 문서, 연습 문제, Q&A
- 휴지통 관리

각 기능마다 별도의 화면이 필요합니다. 만약 모든 걸 한 페이지에 넣으면 너무 복잡해지겠죠? 그래서 페이지를 나누고, 각 페이지마다 고유한 주소(URL)를 부여했습니다. 사용자가 특정 태스크의 주소를 북마크하거나 공유할 수도 있게요.

---

## 어떻게 작동하나요?

### 라우트(경로) 구조

우리가 만든 7개의 경로입니다:

1. **`/`** - 대시보드 (프로젝트 목록)
   - 로그인하면 처음 보이는 화면
   - 내가 만든 프로젝트들을 볼 수 있습니다

2. **`/register`** - 회원가입 페이지
   - 새로운 사용자가 계정을 만듭니다

3. **`/login`** - 로그인 페이지
   - 기존 사용자가 로그인합니다

4. **`/projects/:id`** - 프로젝트 상세 페이지
   - 특정 프로젝트의 태스크들을 봅니다
   - `:id` 부분은 숫자로 바뀝니다 (예: `/projects/123`)

5. **`/tasks/:id`** - 태스크 상세 페이지
   - 학습 문서, 연습 문제, Q&A 탭이 있습니다
   - 이 프로젝트의 핵심 학습 화면입니다

6. **`/trash`** - 휴지통 페이지
   - 삭제한 프로젝트와 태스크를 관리합니다

7. **`*`** - 404 에러 페이지
   - 존재하지 않는 주소를 입력하면 보입니다
   - 대시보드로 돌아가는 링크가 있습니다

### 테스트 가능한 구조

개발 시 테스트를 쉽게 하려고 라우터를 두 부분으로 나눴습니다:

- **`main.tsx`**: 실제 앱에서 사용하는 `BrowserRouter` (진짜 주소창 사용)
- **`App.tsx`**: 경로들만 정의 (테스트에서는 `MemoryRouter`로 감싸서 테스트)

이렇게 하면 테스트할 때 실제 브라우저 주소창 없이도 경로 이동을 시뮬레이션할 수 있습니다.

---

## 어떻게 테스트했나요?

**TDD 방식**으로 개발했습니다:

### 🔴 RED 단계

먼저 7개 페이지의 placeholder 컴포넌트를 만들었습니다:
- `Register.tsx`, `Login.tsx`, `Dashboard.tsx`
- `ProjectDetail.tsx`, `TaskDetail.tsx`, `Trash.tsx`
- `NotFound.tsx` (404 페이지)

각 페이지는 간단한 제목과 "Phase X에서 구현될 예정입니다" 메시지만 표시합니다.

그 다음 8개의 테스트를 작성했습니다:
- 대시보드가 `/`에서 렌더링되는지
- 회원가입 페이지가 `/register`에서 렌더링되는지
- 로그인 페이지가 `/login`에서 렌더링되는지
- 프로젝트 상세가 `/projects/123`에서 렌더링되는지
- 태스크 상세가 `/tasks/456`에서 렌더링되는지
- 휴지통이 `/trash`에서 렌더링되는지
- 404 페이지가 잘못된 주소에서 표시되는지
- 404 페이지에 대시보드 링크가 있는지

테스트를 돌렸더니 모두 실패! (아직 라우터를 설정 안 했으니까요)

### 🟢 GREEN 단계

`App.tsx`와 `main.tsx`를 수정해서 React Router를 설정했습니다:

```typescript
// main.tsx - 실제 앱에서 BrowserRouter로 감싸기
<BrowserRouter>
  <App />
</BrowserRouter>

// App.tsx - 경로들만 정의
<Routes>
  <Route path="/register" element={<Register />} />
  <Route path="/login" element={<Login />} />
  <Route path="/" element={<Dashboard />} />
  {/* ... 나머지 경로들 */}
</Routes>
```

테스트를 다시 돌렸더니 8개 모두 통과! ✅

---

## 수정/생성된 파일

**생성된 파일:**
- `frontend/src/pages/Register.tsx` - 회원가입 페이지
- `frontend/src/pages/Login.tsx` - 로그인 페이지
- `frontend/src/pages/Dashboard.tsx` - 대시보드
- `frontend/src/pages/ProjectDetail.tsx` - 프로젝트 상세
- `frontend/src/pages/TaskDetail.tsx` - 태스크 상세
- `frontend/src/pages/Trash.tsx` - 휴지통
- `frontend/src/pages/NotFound.tsx` - 404 페이지
- `frontend/src/test/App.test.tsx` - 라우팅 테스트 (8개)

**수정된 파일:**
- `frontend/src/App.tsx` - Routes 정의 추가
- `frontend/src/main.tsx` - BrowserRouter 래퍼 추가

**사용된 기술:**
- React Router v6.20.1 - 클라이언트 사이드 라우팅
- React Testing Library - 컴포넌트 테스트

---

## 관련 개념

**클라이언트 사이드 라우팅(Client-Side Routing)**: 페이지 이동 시 서버에 새로 요청하지 않고, JavaScript로 화면만 바꾸는 방식입니다. 페이지 전환이 빠르고 부드럽습니다.

**동적 라우트(Dynamic Route)**: `/projects/:id`처럼 `:id` 부분이 변하는 경로입니다. 123번 프로젝트는 `/projects/123`, 456번은 `/projects/456`처럼 사용됩니다.

**SPA (Single Page Application)**: 실제로는 하나의 HTML 파일만 로드하지만, React Router로 여러 페이지처럼 보이게 만드는 앱입니다.

---

## 주의사항

1. **Router 중첩 금지**: `BrowserRouter` 안에 또 다른 `BrowserRouter`를 넣으면 안 됩니다. 그래서 `main.tsx`에만 `BrowserRouter`를 두고, `App.tsx`는 `Routes`만 사용합니다.

2. **테스트 시 MemoryRouter 사용**: 테스트할 때는 실제 브라우저 주소창이 없으므로 `MemoryRouter`를 사용해서 경로를 시뮬레이션합니다.

3. **Placeholder 페이지**: 지금 만든 페이지들은 모두 껍데기입니다. 실제 기능은 Phase 3~10에서 순차적으로 구현됩니다.

---

## 다음 단계

이제 길은 만들어졌으니, 각 방(페이지)을 채울 차례입니다:

1. **T019**: TanStack Query 설정 - API 호출과 캐싱 관리
2. **T020**: Axios API 클라이언트 - 백엔드와 통신
3. **T021**: Zustand 인증 스토어 - 로그인 상태 관리
4. **T022**: Tailwind CSS + shadcn/ui - 예쁜 UI 컴포넌트

그 다음 Phase 3에서 실제 회원가입/로그인 기능을 구현하면서, 이 페이지들에 생명을 불어넣을 것입니다!
