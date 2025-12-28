# TASK-091: Gemini API 클라이언트 래퍼 구현

## 무엇을 만들었나요?

Google의 Gemini AI API를 사용하기 위한 클라이언트 래퍼를 만들었습니다. 마치 전화 통역사 같은 역할을 하는 코드예요. 우리 앱이 "이 코드를 설명해줘"라고 요청하면, 이 클라이언트가 그 요청을 Gemini AI가 이해할 수 있는 형태로 변환해서 보내고, AI의 답변을 다시 우리 앱이 사용할 수 있는 형태로 바꿔주는 거죠.

## 왜 이렇게 만들었나요?

### 1. 재시도 로직 (Retry Logic)
인터넷 전화를 할 때 가끔 연결이 안 되면 다시 거는 것처럼, AI API도 가끔 응답을 못 받을 때가 있어요. 그래서 실패하면 자동으로 3번까지 다시 시도하도록 했습니다. 재시도할 때마다 기다리는 시간을 2배씩 늘려서(지수 백오프) 서버에 부담을 주지 않도록 했어요.

### 2. 콘텐츠 타입별 설정
- **문서 생성**: 긴 응답이 필요하니까 8192 토큰까지 허용
- **연습문제**: 중간 길이 4096 토큰
- **Q&A**: 빠른 답변이 필요하니까 2048 토큰으로 제한

이렇게 하면 각 용도에 맞게 AI가 최적의 답변을 생성할 수 있어요.

### 3. 안전 설정 (Safety Settings)
초보자를 위한 교육 콘텐츠니까 부적절한 내용이 생성되지 않도록 안전 필터를 설정했습니다.

## 어떻게 작동하나요?

```python
# 1. 환경변수에서 설정 불러오기
config = GeminiConfig.from_env()

# 2. 클라이언트 생성
client = GeminiClient(config)

# 3. 문서 생성 요청
response = await client.generate_document(
    code="def hello(): print('안녕')",
    language="Python"
)

# 4. 결과 사용
print(response.json_content)  # 7장 구조의 학습 문서
```

## 어떤 파일을 만들었나요?

1. `backend/src/services/ai/__init__.py` - AI 서비스 패키지 초기화
2. `backend/src/services/ai/gemini_client.py` - 메인 클라이언트 구현
3. `backend/requirements.txt` - google-generativeai 의존성 추가

## 주요 기능

- **GeminiConfig**: 환경변수에서 API 키, 모델명, 타임아웃 등 설정 로드
- **GeminiClient.generate()**: 범용 콘텐츠 생성
- **GeminiClient.generate_document()**: 7장 구조 학습 문서 생성
- **GeminiClient.generate_qa_response()**: Q&A 답변 생성
- **GeminiClient.health_check()**: API 연결 상태 확인

## 에러 처리

- **GeminiError**: 기본 에러
- **GeminiRateLimitError**: API 호출 한도 초과시
- **GeminiContentFilterError**: 콘텐츠가 안전 필터에 걸렸을 때
- **GeminiTimeoutError**: 응답 시간 초과시

## 관련 개념

- **비동기 프로그래밍**: `async/await`를 사용해서 API 호출 중에도 다른 작업 가능
- **지수 백오프**: 재시도 간격을 점점 늘려서 서버 부하 방지
- **JSON 모드**: AI가 구조화된 JSON 형태로 응답하도록 설정

## 다음 단계

- T092: 7장 문서 생성을 위한 프롬프트 템플릿 구현
- T093: 문서 생성 서비스에서 이 클라이언트 사용
- T094: Celery 비동기 태스크에서 문서 생성 실행
