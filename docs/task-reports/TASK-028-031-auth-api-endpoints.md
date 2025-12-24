# TASK-028 ~ T031: 인증 API 엔드포인트

**날짜**: 2025-12-24 (문서 정리)
**상태**: 완료
**태스크**: T028, T029, T030, T031

---

## 무엇을 만들었나요?

사용자 인증을 위한 백엔드 API 엔드포인트를 구현했습니다. 웹사이트에 "회원가입", "로그인", "로그아웃" 버튼을 눌렀을 때 서버에서 처리하는 부분입니다.

---

## 포함된 태스크

| Task | 엔드포인트 | 설명 |
|------|-----------|------|
| T028 | POST /auth/register | 새 사용자 회원가입 |
| T029 | POST /auth/login | 로그인 및 토큰 발급 |
| T030 | POST /auth/logout | 로그아웃 (토큰 무효화) |
| T031 | POST /auth/refresh | 액세스 토큰 갱신 |

※ T029A (GET /auth/me)는 별도 보고서에 문서화됨

---

## API 상세

### POST /auth/register (T028)
**목적**: 새 사용자 계정 생성

```json
// 요청
{
  "email": "user@example.com",
  "password": "securePassword123"
}

// 응답 (201 Created)
{
  "id": "uuid",
  "email": "user@example.com",
  "skill_level": "Complete Beginner"
}
```

### POST /auth/login (T029)
**목적**: 로그인 후 JWT 토큰 발급

```json
// 요청
{
  "email": "user@example.com",
  "password": "securePassword123"
}

// 응답 (200 OK) + Set-Cookie 헤더
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### POST /auth/logout (T030)
**목적**: 리프레시 토큰 무효화 및 쿠키 삭제

```json
// 응답 (200 OK)
{
  "message": "Successfully logged out"
}
```

### POST /auth/refresh (T031)
**목적**: 만료된 액세스 토큰 갱신

리프레시 토큰(쿠키)을 사용하여 새 액세스 토큰 발급

---

## 파일 위치

```
backend/src/api/auth.py
```

---

## 보안 고려사항

1. **비밀번호**: bcrypt로 해시하여 저장 (절대 평문 저장 안함)
2. **JWT 토큰**:
   - 액세스 토큰: 15분 유효 (짧게)
   - 리프레시 토큰: 7일 유효 (길게, HttpOnly 쿠키)
3. **HTTPS**: 프로덕션에서 필수 (토큰 탈취 방지)

---

## 테스트

```bash
# 단위 테스트 실행
cd backend
python -m pytest tests/unit/api/test_auth.py -v
```

---

## 다음 단계

- T032-T038: 프론트엔드 인증 UI 구현
