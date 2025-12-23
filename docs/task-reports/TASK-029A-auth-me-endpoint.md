# T029A: GET /auth/me 현재 사용자 조회 엔드포인트 구현

## 작업 요약
로그인된 사용자 정보를 조회하는 API 엔드포인트와 프론트엔드 인증 상태 복원 로직을 구현했습니다.

## 문제 상황
1. 로그인하지 않은 상태에서 `/dashboard`로 직접 접근 가능 (ProtectedRoute 미사용)
2. 로그인 후에도 dashboard 접근 불가 (auth-store 미업데이트)
3. 페이지 새로고침 시 인증 상태 유실 (쿠키에 토큰 있어도 store 초기화)

## 구현 내용

### 1. Backend: GET /auth/me 엔드포인트
**파일**: `backend/src/api/auth.py`

```python
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
```

- `get_current_user` 의존성으로 access_token 쿠키 검증
- 유효한 토큰 → 사용자 정보 반환
- 유효하지 않은 토큰 → 401 Unauthorized

### 2. Frontend: authService.getMe() 추가
**파일**: `frontend/src/services/auth-service.ts`

```typescript
async getMe(): Promise<User> {
  const response = await apiClient.get<UserResponse>('/auth/me')
  return transformUser(response.data)
}
```

### 3. Frontend: AuthProvider 생성
**파일**: `frontend/src/components/auth/AuthProvider.tsx`

- 앱 시작 시 `authService.getMe()` 호출
- 성공 → auth-store에 user 설정 (isAuthenticated = true)
- 실패 → auth-store 초기화 (isAuthenticated = false)
- 초기화 완료 전까지 null 렌더링 (깜빡임 방지)

### 4. Frontend: Login.tsx 수정
**파일**: `frontend/src/pages/Login.tsx`

- `authService.login` → `useAuth().login` 변경
- 로그인 성공 시 auth-store 자동 업데이트
- 원래 가려던 페이지로 리다이렉트 (location.state.from)

### 5. Frontend: App.tsx 수정
**파일**: `frontend/src/App.tsx`

- ProtectedRoute import 및 적용
- 보호 대상: `/`, `/dashboard`, `/projects/:id`, `/tasks/:id`, `/trash`

### 6. Frontend: main.tsx 수정
**파일**: `frontend/src/main.tsx`

- AuthProvider로 App 감싸기

## 왜 이렇게 구현했나요?

**GET /auth/me vs POST /auth/refresh**:
- `/auth/me`: 사용자 정보만 조회 (토큰 변경 없음)
- `/auth/refresh`: 토큰 갱신 (rotation 발생)
- 페이지 로드마다 토큰 갱신은 불필요하고 위험할 수 있음

**AuthProvider 패턴**:
- 앱 전체에서 일관된 인증 상태 보장
- 초기화 완료 전까지 렌더링 차단으로 깜빡임 방지
- React Context 없이 Zustand로 간단하게 구현

## 어떻게 작동하나요?

### 최초 로그인 흐름
1. 사용자가 이메일/비밀번호 입력
2. POST /auth/login → 쿠키에 토큰 저장
3. `useAuth().login`이 auth-store 업데이트
4. ProtectedRoute가 isAuthenticated=true 확인
5. Dashboard 렌더링

### 페이지 새로고침 흐름
1. AuthProvider 마운트
2. GET /auth/me 호출 (access_token 쿠키 자동 전송)
3. 성공 → auth-store에 user 설정
4. ProtectedRoute가 isAuthenticated=true 확인
5. Dashboard 유지

### 비로그인 상태 접근 흐름
1. AuthProvider 마운트
2. GET /auth/me 호출 (쿠키 없음)
3. 401 응답 → auth-store 초기화
4. ProtectedRoute가 isAuthenticated=false 확인
5. /login으로 리다이렉트

## 수정된 파일
- `backend/src/api/auth.py` - GET /auth/me 엔드포인트 추가
- `frontend/src/services/auth-service.ts` - getMe() 메서드 추가
- `frontend/src/components/auth/AuthProvider.tsx` - 신규 생성
- `frontend/src/components/auth/ProtectedRoute.tsx` - 기존 (변경 없음)
- `frontend/src/pages/Login.tsx` - useAuth hook 사용으로 변경
- `frontend/src/App.tsx` - ProtectedRoute 적용
- `frontend/src/main.tsx` - AuthProvider 적용
- `specs/001-code-learning-platform/tasks.md` - T029A 추가

## 실생활 비유
호텔 체크인과 비슷합니다:
- 로그인 = 체크인 (카드키 발급)
- GET /auth/me = 카드키로 객실 확인 (투숙객 정보 조회)
- 페이지 새로고침 = 호텔 재방문 시 카드키로 본인 확인

## 다음 단계
- T039-T042: 브라우저 수동 테스트로 전체 인증 흐름 검증
