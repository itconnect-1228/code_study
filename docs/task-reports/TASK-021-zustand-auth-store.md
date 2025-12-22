# Task 021: Zustand 인증 상태 관리 스토어 구현

**작성일**: 2025-12-08
**작업 유형**: Frontend Foundation
**TDD 사이클**: ✅ RED → GREEN → REFACTOR 완료

## 무엇을 만들었나요?

사용자의 로그인 상태를 프론트엔드에서 관리하는 "상태 관리 저장소"를 만들었습니다. 이것은 마치 쇼핑몰의 고객 명부와 같아서, 현재 로그인한 사용자가 누구인지, 로그인되어 있는지, 지금 로그인 중인지 등의 정보를 앱 전체에서 공유할 수 있게 해줍니다.

## 왜 이렇게 만들었나요?

### 전역 상태 관리의 필요성
React 앱에서 여러 페이지와 컴포넌트가 "현재 로그인한 사용자가 누구인가?"라는 정보를 알아야 합니다. 예를 들어:
- 헤더에 "환영합니다, 홍길동님" 표시
- 로그인 안 했으면 대시보드 접근 차단
- 프로필 페이지에서 사용자 정보 표시

만약 이 정보를 각 컴포넌트마다 따로 관리한다면, 로그인할 때마다 모든 컴포넌트를 일일이 업데이트해야 합니다. 하지만 Zustand 스토어를 사용하면, 한 곳에서 상태를 업데이트하면 이를 사용하는 모든 컴포넌트가 자동으로 새로운 정보를 받습니다.

### Zustand를 선택한 이유
Redux, MobX, Recoil 등 다양한 상태 관리 라이브러리가 있지만 Zustand를 선택한 이유는:
- **간단함**: Redux처럼 복잡한 설정이 필요 없음
- **작은 크기**: 라이브러리 자체가 매우 가벼움 (~1KB)
- **TypeScript 지원**: 타입 안정성이 뛰어남
- **개발자 도구 지원**: Redux DevTools로 디버깅 가능

### JWT는 쿠키에, 상태는 메모리에
중요한 점: 실제 JWT 토큰은 HTTPOnly 쿠키에 저장되고 브라우저가 자동으로 관리합니다. 이 스토어는 "UI에서 보여줄 사용자 정보"만 관리합니다. 이렇게 분리하는 이유는:
- **보안**: 쿠키는 JavaScript로 접근 불가 (XSS 공격 방지)
- **편의성**: 사용자 정보는 UI에서 쉽게 접근 가능
- **자동 관리**: 브라우저가 쿠키를 자동으로 요청에 포함

## 어떻게 작동하나요?

### 1. 상태(State) 구조
```typescript
interface AuthState {
  user: User | null;           // 현재 로그인한 사용자 정보
  isAuthenticated: boolean;    // 로그인 여부
  isLoading: boolean;          // 로그인/로그아웃 처리 중 여부
}
```

### 2. 액션(Actions) 함수들

#### setUser(user)
사용자 정보를 설정하고 로그인 상태를 업데이트합니다.
```typescript
// 로그인 성공 시
setUser({
  id: '123',
  email: 'user@example.com',
  createdAt: '2024-01-01'
});
// → isAuthenticated가 자동으로 true로 변경됨
```

#### setLoading(loading)
로그인/로그아웃 처리 중임을 표시합니다.
```typescript
setLoading(true);  // 로딩 스피너 표시
// ... API 호출 ...
setLoading(false); // 로딩 스피너 숨김
```

#### clearAuth()
로그아웃 시 모든 인증 상태를 초기화합니다.
```typescript
clearAuth();
// → user: null, isAuthenticated: false, isLoading: false
```

### 3. 사용 예시

#### 기본 사용법
```typescript
import { useAuthStore } from '@/stores/auth-store';

function Dashboard() {
  const { user, isAuthenticated, setUser } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return <h1>환영합니다, {user.email}님!</h1>;
}
```

#### 최적화된 사용법 (선택자 훅)
```typescript
import { useUser, useIsAuthenticated } from '@/stores/auth-store';

function Header() {
  // user만 필요하므로 user만 구독
  // isAuthenticated가 변경되어도 이 컴포넌트는 리렌더링 안 됨
  const user = useUser();

  return <div>환영합니다, {user?.email}님!</div>;
}

function ProtectedRoute({ children }) {
  // isAuthenticated만 필요하므로 이것만 구독
  const isAuthenticated = useIsAuthenticated();

  return isAuthenticated ? children : <Navigate to="/login" />;
}
```

### 4. 개발자 도구 통합
REFACTOR 단계에서 Zustand DevTools를 추가했습니다. 이제 개발 중에:
- Redux DevTools로 상태 변화 추적 가능
- 각 액션의 이름 표시 (auth/setUser, auth/clearAuth 등)
- 타임 트래블 디버깅 지원
- **프로덕션에서는 자동 비활성화** (성능 영향 없음)

## 어떻게 테스트했나요? (TDD 사이클)

### 🔴 RED 단계: 실패하는 테스트 작성
10개의 테스트를 작성했습니다:

1. **초기 상태 테스트** (3개)
   - user가 null인가?
   - isAuthenticated가 false인가?
   - isLoading이 false인가?

2. **setUser 동작 테스트** (2개)
   - 사용자 설정 시 isAuthenticated가 true가 되는가?
   - null 설정 시 isAuthenticated가 false가 되는가?

3. **setLoading 동작 테스트** (2개)
   - true/false 토글이 제대로 작동하는가?

4. **clearAuth 동작 테스트** (1개)
   - 모든 상태가 초기화되는가?

5. **상태 지속성 테스트** (1개)
   - 여러 번 접근해도 같은 상태를 유지하는가?

6. **타입 안정성 테스트** (1개)
   - User 타입이 올바르게 작동하는가?

### 🟢 GREEN 단계: 최소한의 구현
모든 테스트를 통과하는 기본 구현을 완성했습니다.

### 🔵 REFACTOR 단계: 코드 개선
세 가지 개선 사항을 추가했습니다:

1. **DevTools 미들웨어 추가**
   - 개발 중 상태 디버깅 용이
   - 각 액션에 의미 있는 이름 부여

2. **선택자 훅 추가**
   - `useUser()`: user만 필요할 때 사용
   - `useIsAuthenticated()`: 인증 상태만 필요할 때 사용
   - `useAuthLoading()`: 로딩 상태만 필요할 때 사용
   - **성능 최적화**: 필요한 부분만 구독하여 불필요한 리렌더링 방지

3. **액션 이름 추가**
   - "auth/setUser", "auth/setLoading", "auth/clearAuth"
   - DevTools에서 어떤 액션이 실행되었는지 명확히 표시

## 수정된 파일들

### 생성된 파일
- `frontend/src/stores/auth-store.ts` (111줄) - Zustand 인증 스토어
- `frontend/src/stores/auth-store.test.ts` (129줄) - 단위 테스트
- `docs/task-reports/TASK-021-zustand-auth-store.md` - 이 문서

### 수정된 파일
- `specs/001-code-learning-platform/tasks.md` - T021을 완료로 표시

## 관련 개념

### 상태 관리(State Management)란?
여러 컴포넌트가 공유해야 하는 데이터를 중앙에서 관리하는 것입니다. 은행의 중앙 데이터베이스처럼, 모든 지점(컴포넌트)이 같은 고객 정보(상태)를 보도록 보장합니다.

### 선택자(Selector)란?
스토어에서 필요한 부분만 골라 가져오는 함수입니다. 마치 백화점에서 필요한 물건만 사는 것처럼, 전체 상태가 아닌 필요한 부분만 구독합니다. 이렇게 하면:
- **성능 향상**: 관련 없는 상태 변경에 리렌더링 안 함
- **코드 명확성**: 컴포넌트가 어떤 상태를 사용하는지 명확함

### 미들웨어(Middleware)란?
상태 변경 과정 중간에 끼어들어 부가 기능을 제공하는 것입니다. DevTools 미들웨어는 상태 변경을 기록하고 시각화해서 디버깅을 돕습니다.

## 주의사항

1. **쿠키와 스토어의 역할 분리**
   - JWT 토큰: HTTPOnly 쿠키에 저장 (보안)
   - 사용자 정보: Zustand 스토어에 저장 (편의성)
   - 절대 JWT 토큰을 스토어에 저장하지 말 것 (XSS 취약점)

2. **페이지 새로고침 시 상태 초기화**
   - Zustand 스토어는 메모리에만 존재
   - 새로고침하면 user 정보가 사라짐
   - 해결: 앱 시작 시 "현재 사용자" API 호출 필요 (T023-T027에서 구현 예정)

3. **DevTools는 개발 모드에서만**
   - `enabled: import.meta.env.DEV` 설정으로 프로덕션에서 자동 비활성화
   - 성능 영향 없음

## 다음 단계

- **T022**: Tailwind CSS와 shadcn/ui 컴포넌트 설정
- **T023-T027**: 실제 인증 로직 구현 (이 스토어를 사용)
  - 로그인 시 `setUser()` 호출
  - 로그아웃 시 `clearAuth()` 호출
  - API 호출 중 `setLoading()` 사용
- **T037**: 보호된 라우트 구현 (`useIsAuthenticated` 활용)
- **향후**: 로그인 상태 영속성 (localStorage + 토큰 갱신)
