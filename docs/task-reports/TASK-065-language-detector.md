# TASK-065: Pygments를 이용한 언어 감지 서비스 구현

## 무엇을 만들었나요?

코드 파일이 어떤 프로그래밍 언어로 작성되었는지 자동으로 알아내는 서비스를 만들었습니다. 마치 번역가가 문서를 보고 "이건 영어로 쓰여있네요" 또는 "이건 일본어입니다"라고 판단하는 것처럼, 이 서비스는 코드를 보고 "이건 Python이네요" 또는 "이건 JavaScript입니다"라고 알려줍니다.

## 왜 이렇게 만들었나요?

사용자가 코드를 업로드하면, 시스템이 어떤 언어인지 알아야 적절한 학습 문서를 생성할 수 있습니다. 예를 들어 Python 코드에 대해서는 Python 문법을 설명해야 하고, JavaScript 코드에 대해서는 JavaScript 문법을 설명해야 하기 때문입니다.

**Pygments 라이브러리를 선택한 이유:**
1. **500개 이상의 언어 지원** - Python, JavaScript, Java, C++ 등 대부분의 프로그래밍 언어를 인식
2. **검증된 안정성** - 10년 이상 사용된 업계 표준 라이브러리
3. **두 가지 감지 방법** - 파일 확장자(.py, .js)와 코드 내용 분석을 모두 지원

## 어떻게 동작하나요?

언어를 감지하는 데는 두 가지 방법이 있습니다:

### 1. 파일 이름으로 감지 (가장 정확함)
- `script.py` → Python
- `app.js` → JavaScript
- `Main.java` → Java

마치 책의 표지를 보고 내용을 짐작하는 것과 같습니다. `.py`라고 적혀 있으면 Python 책이라고 바로 알 수 있죠.

### 2. 코드 내용으로 감지 (파일명이 없을 때)
- `#!/usr/bin/env python3`로 시작하면 → Python
- `function()`, `const`, `=>` 같은 패턴이면 → JavaScript
- `public class`로 시작하면 → Java

마치 책을 펼쳐서 몇 문장을 읽고 "이건 소설이구나" 또는 "이건 요리책이구나"라고 판단하는 것과 같습니다.

## 테스트는 어떻게 했나요?

**TDD(테스트 주도 개발) 방식으로 63개의 테스트를 작성했습니다:**

1. **파일 확장자 테스트** - 20가지 주요 프로그래밍 언어 (Python, JavaScript, TypeScript, Java, C++, Go, Rust 등)
2. **코드 내용 분석 테스트** - shebang(#!)이 있는 코드, HTML 구조 감지
3. **특수 상황 테스트** - 빈 파일, 알 수 없는 확장자, Windows 경로 등
4. **통합 테스트** - 파일 업로드와 붙여넣기 시나리오

모든 테스트가 통과했습니다: `63 passed in 0.45s`

## 수정된 파일들

| 파일 경로 | 변경 내용 |
|---------|---------|
| `backend/requirements.txt` | Pygments 라이브러리 의존성 추가 |
| `backend/src/services/code_analysis/__init__.py` | 새 패키지 초기화 |
| `backend/src/services/code_analysis/language_detector.py` | **핵심 구현** - 언어 감지 함수들 |
| `backend/tests/unit/services/code_analysis/test_language_detector.py` | 63개 단위 테스트 |

## 주요 함수들

- `detect_language(filename, content)` - 파일명과 내용으로 언어 감지
- `detect_language_by_filename(filename)` - 파일 확장자로 감지
- `detect_language_by_content(content)` - 코드 내용 분석으로 감지
- `get_supported_languages()` - 지원하는 모든 언어 목록
- `get_language_by_name(name)` - 이름으로 언어 정보 조회

## 알아두면 좋은 점

1. **파일 확장자가 가장 정확합니다** - 내용 분석은 보조 수단으로 사용
2. **대소문자 주의** - Pygments는 `.PY`와 `.py`를 다르게 처리할 수 있음
3. **TSX는 TypeScript와 별개** - Pygments는 `.tsx` 파일을 "TSX"로, `.ts`를 "TypeScript"로 구분
4. **내용 분석의 한계** - 짧은 코드나 주석만 있는 경우 정확도가 떨어질 수 있음

## 다음 단계

- T066: 코드 복잡도 분석기 구현 - 코드가 얼마나 복잡한지 측정하는 서비스
- T067: 파일 저장 서비스 - 업로드된 코드를 서버에 저장하는 기능
