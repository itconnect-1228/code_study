# Task 019: TanStack Query 클라이언트 설정

**작업 완료일**: 2025-12-21
**관련 이슈**: Phase 2 - Frontend Foundation
**TDD 사이클**: RED → GREEN

---

## 무엇을 만들었나요?

서버에서 데이터를 가져오고 관리하는 TanStack Query (React Query)를 설정했습니다. 이는 API 호출을 자동으로 캐싱하고, 로딩 상태를 관리하며, 실패한 요청을 재시도하는 똑똑한 데이터 관리자입니다.

냉장고를 생각해보세요. 매번 마트에 가서 우유를 사는 대신, 냉장고에 우유를 보관해두고 필요할 때 꺼내 먹죠. 우유가 상했는지 확인해서 필요하면 새로 사러 가고요. TanStack Query는 이런 냉장고 같은 역할을 합니다. 서버에서 가져온 데이터를 캐시에 저장해두고, 필요할 때 바로 보여주며, 오래된 데이터는 자동으로 새로 가져옵니다.

---

## 왜 이렇게 만들었나요?

일반적으로 React 앱에서 API를 호출하려면:
1. `useState`로 로딩 상태 관리
2. `useState`로 에러 상태 관리
3. `useState`로 데이터 저장
4. `useEffect`로 API 호출
5. 캐싱 로직 직접 구현
6. 재시도 로직 직접 구현

이렇게 하면 코드가 길고 복잡해지며, 같은 데이터를 여러 번 요청하게 됩니다.

TanStack Query를 사용하면:
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['projects'],
  queryFn: fetchProjects
});
```

단 3줄로 끝! 로딩, 에러, 캐싱, 재시도를 모두 자동으로 처리해줍니다.

---

## 어떻게 작동하나요?

### 설정한 옵션들

1. **StaleTime: 5분**
   - 데이터가 "신선한" 상태로 유지되는 시간
   - 5분 동안은 같은 데이터를 다시 요청하지 않음
   - 예: 프로젝트 목록을 한 번 불러오면 5분 동안은 캐시에서 바로 보여줌

2. **GcTime (Garbage Collection Time): 10분**
   - 사용하지 않는 캐시 데이터를 보관하는 시간
   - 10분 동안 안 쓴 데이터는 메모리에서 제거
   - 메모리 낭비 방지

3. **Retry: 3회**
   - 네트워크 요청이 실패하면 3번까지 재시도
   - 지수 백오프 적용 (1초, 2초, 4초 대기 후 재시도)
   - 일시적인 네트워크 문제 자동 해결

4. **RefetchOnWindowFocus: 비활성화**
   - 사용자가 다른 탭에서 돌아와도 자동으로 새로고침 안 함
   - 깜빡이는 화면 없이 부드러운 UX
   - 필요할 때만 수동으로 새로고침

### Provider 구조

```typescript
<QueryClientProvider client={queryClient}>
  <BrowserRouter>
    <App />
  </BrowserRouter>
</QueryClientProvider>
```

- `QueryClientProvider`가 전체 앱을 감싸서 모든 컴포넌트에서 사용 가능
- `BrowserRouter` 밖에 배치해서 라우터와 독립적으로 작동

---

## 어떻게 테스트했나요?

**TDD 방식**으로 개발했습니다:

### 🔴 RED 단계

두 종류의 테스트를 작성했습니다:

**설정 테스트 (main.test.tsx - 6개)**
- QueryClient가 올바른 옵션으로 생성되는지
- StaleTime이 5분으로 설정되었는지
- GcTime이 10분으로 설정되었는지
- Retry가 3회로 설정되었는지
- RefetchOnWindowFocus가 비활성화되었는지
- QueryClientProvider가 앱을 감싸는지

**통합 테스트 (query-integration.test.tsx - 3개)**
- 컴포넌트에서 useQuery 훅을 사용할 수 있는지
- 쿼리 결과가 캐시에 저장되는지
- 에러가 발생해도 gracefully 처리되는지

모든 테스트가 통과! (TanStack Query의 API 자체를 테스트했으므로)

### 🟢 GREEN 단계

`main.tsx`에 QueryClient를 생성하고 QueryClientProvider로 앱을 감쌌습니다.

모든 테스트가 여전히 통과! 총 17개 테스트 성공 (6 + 3 + 8 Router 테스트)

---

## 수정/생성된 파일

**생성된 파일:**
- `frontend/src/test/query-client.test.tsx` - QueryClient 설정 및 통합 테스트 (7개)

**수정된 파일:**
- `frontend/src/main.tsx` - QueryClient 생성 및 Provider 추가

**사용된 기술:**
- TanStack Query v5.14.2 (React Query v5)
- React 18.2.0

---

## 실제 사용 예시

이제 컴포넌트에서 이렇게 쉽게 API를 호출할 수 있습니다:

```typescript
import { useQuery } from '@tanstack/react-query';

function ProjectList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const response = await fetch('/api/projects');
      return response.json();
    }
  });

  if (isLoading) return <div>로딩 중...</div>;
  if (error) return <div>에러 발생!</div>;

  return (
    <ul>
      {data.map(project => (
        <li key={project.id}>{project.name}</li>
      ))}
    </ul>
  );
}
```

---

## 관련 개념

**캐싱(Caching)**: 한 번 가져온 데이터를 메모리에 저장해두고 재사용하는 기술입니다. 마트에서 장을 봐서 냉장고에 보관하는 것과 같습니다.

**낙관적 업데이트(Optimistic Update)**: 서버 응답을 기다리지 않고 먼저 화면을 업데이트하는 방식입니다. 좋아요 버튼을 누르면 바로 색이 바뀌고, 나중에 서버에 저장되는 것처럼요.

**지수 백오프(Exponential Backoff)**: 재시도 시 대기 시간을 점점 늘리는 전략입니다. 1초, 2초, 4초... 이렇게요. 서버가 과부하 상태일 때 더 쉬게 해주는 배려입니다.

**자동 중복 제거(Request Deduplication)**: 같은 데이터를 동시에 여러 번 요청하면 실제로는 한 번만 요청하고 결과를 공유합니다.

---

## TanStack Query의 주요 장점

1. **자동 캐싱**: 한 번 가져온 데이터를 저장해서 빠르게 보여줌
2. **로딩 상태 관리**: `isLoading`으로 쉽게 로딩 UI 표시
3. **에러 처리**: `error` 객체로 에러 핸들링 간단
4. **자동 재시도**: 네트워크 오류 시 자동으로 재시도
5. **백그라운드 업데이트**: 사용자가 모르게 최신 데이터 유지
6. **메모리 최적화**: 안 쓰는 캐시는 자동 삭제
7. **요청 취소**: 컴포넌트가 unmount되면 요청 자동 취소

---

## 주의사항

1. **QueryKey의 중요성**: `queryKey`는 캐시의 주소입니다. 같은 키를 쓰면 같은 캐시를 공유합니다.

2. **StaleTime vs GcTime**:
   - StaleTime: 데이터가 "신선한" 시간
   - GcTime: 캐시를 "보관하는" 시간
   - StaleTime이 지나도 캐시는 남아있고, GcTime이 지나야 삭제됩니다

3. **개발자 도구**: TanStack Query DevTools를 추가하면 캐시 상태를 시각적으로 볼 수 있습니다 (Phase 11에서 추가 예정)

---

## 다음 단계

이제 데이터 캐싱 시스템이 준비되었으니:

1. **T020**: Axios API 클라이언트 - 실제 백엔드와 통신할 HTTP 클라이언트
2. **T021**: Zustand 인증 스토어 - 로그인 상태 관리
3. **T022**: Tailwind CSS + shadcn/ui - 예쁜 UI 컴포넌트

그 다음 Phase 3에서 실제로 TanStack Query를 사용해서 로그인, 프로젝트 목록, 태스크 데이터를 불러오게 됩니다!

TanStack Query는 이 프로젝트의 모든 API 호출에서 사용될 핵심 라이브러리입니다. 🚀
