# TASK-020: API 클라이언트 기본 설정

**날짜**: 2025-12-24 (문서 정리)
**상태**: 완료

---

## 무엇을 만들었나요?

프론트엔드에서 백엔드 API를 호출하기 위한 기본 HTTP 클라이언트를 설정했습니다. 마치 전화기처럼, 프론트엔드가 백엔드와 "대화"할 수 있게 해주는 도구입니다.

---

## 왜 이렇게 만들었나요?

### Axios 선택 이유
1. **자동 JSON 변환**: 응답을 자동으로 JavaScript 객체로 변환
2. **인터셉터 지원**: 모든 요청/응답에 공통 처리 가능 (토큰 첨부 등)
3. **에러 처리**: HTTP 에러를 일관되게 처리

### 기본 설정
- **baseURL**: API 서버 주소 (`/api/v1`)
- **withCredentials**: 쿠키 자동 전송 (인증용)
- **timeout**: 요청 타임아웃 설정

---

## 파일 위치

```
frontend/src/services/api-client.ts
```

---

## 코드 예시

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  timeout: 10000,
});

// 요청 인터셉터: 토큰 자동 첨부
apiClient.interceptors.request.use((config) => {
  // 토큰 처리 로직
  return config;
});

// 응답 인터셉터: 에러 처리
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // 401 에러 시 토큰 갱신 등
    return Promise.reject(error);
  }
);

export default apiClient;
```

---

## 관련 개념

### HTTP 클라이언트
브라우저에서 서버로 HTTP 요청을 보내는 도구입니다. `fetch` API를 직접 사용할 수도 있지만, Axios는 더 편리한 기능을 제공합니다.

### 인터셉터
요청이 서버로 가기 전, 또는 응답이 코드로 전달되기 전에 "가로채서" 추가 처리를 할 수 있습니다.

---

## 다음 단계

- T021: Zustand 인증 스토어 설정
- T034: 인증 서비스 구현 (이 클라이언트 사용)
