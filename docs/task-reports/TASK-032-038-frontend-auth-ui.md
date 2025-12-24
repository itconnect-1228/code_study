# TASK-032 ~ T038: 프론트엔드 인증 UI

**날짜**: 2025-12-24 (문서 정리)
**상태**: 완료
**태스크**: T032, T033, T034, T035, T036, T037, T038

---

## 무엇을 만들었나요?

사용자가 회원가입하고 로그인할 수 있는 화면과 그 뒤에서 작동하는 로직을 구현했습니다. 마치 건물의 "출입문"과 "보안 시스템"을 만든 것과 같습니다.

---

## 포함된 태스크

### 컴포넌트 (T032-T033) [P]

| Task | 컴포넌트 | 설명 |
|------|---------|------|
| T032 | RegisterForm | 회원가입 폼 (이메일, 비밀번호 입력) |
| T033 | LoginForm | 로그인 폼 |

### 서비스 (T034)

| Task | 파일 | 설명 |
|------|------|------|
| T034 | auth-service.ts | API 호출 함수 (register, login, logout) |

### 페이지 (T035-T036)

| Task | 페이지 | 경로 |
|------|--------|------|
| T035 | Register.tsx | /register |
| T036 | Login.tsx | /login |

### 보호 & 자동 갱신 (T037-T038)

| Task | 기능 | 설명 |
|------|------|------|
| T037 | ProtectedRoute | 로그인 안 된 사용자 리디렉션 |
| T038 | useAuth hook | 토큰 자동 갱신 로직 |

---

## 파일 구조

```
frontend/src/
├── components/auth/
│   ├── RegisterForm.tsx    # T032
│   ├── LoginForm.tsx       # T033
│   └── ProtectedRoute.tsx  # T037
├── pages/
│   ├── Register.tsx        # T035
│   └── Login.tsx           # T036
├── services/
│   └── auth-service.ts     # T034
└── hooks/
    └── useAuth.ts          # T038
```

---

## 사용자 흐름

### 회원가입
1. 사용자가 `/register` 페이지 방문
2. 이메일, 비밀번호 입력
3. "회원가입" 버튼 클릭
4. 서버에 POST /auth/register 요청
5. 성공 시 로그인 페이지로 이동

### 로그인
1. 사용자가 `/login` 페이지 방문
2. 이메일, 비밀번호 입력
3. "로그인" 버튼 클릭
4. 서버에 POST /auth/login 요청
5. 토큰 받아서 저장 (Zustand 스토어)
6. 대시보드로 이동

### 자동 토큰 갱신 (T038)
- 액세스 토큰이 만료되기 전에 자동으로 갱신
- 사용자는 끊김 없이 서비스 이용 가능

---

## 코드 예시

### ProtectedRoute (T037)

```tsx
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return children;
}
```

### useAuth Hook (T038)

```tsx
function useAuth() {
  // 토큰 상태 관리
  // 자동 갱신 로직
  // 로그인/로그아웃 함수
}
```

---

## 테스트

```bash
# 프론트엔드 테스트
cd frontend
npm run test
```

---

## 다음 단계

- T039-T042: 브라우저 수동 테스트 (실제 동작 확인)
