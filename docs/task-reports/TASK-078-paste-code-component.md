# T078: PasteCode 컴포넌트

## 무엇을 만들었나요?

코드를 직접 붙여넣을 수 있는 React 컴포넌트를 만들었어요. 파일이 없어도 코드 조각을 바로 입력해서 학습할 수 있게 해주는 기능이에요. Stack Overflow에서 코드를 복사해왔을 때 바로 붙여넣기 할 수 있어요.

## 왜 이렇게 만들었나요?

모든 학습 상황에서 파일이 있는 건 아니에요:
- 온라인에서 찾은 코드 조각
- 에러 해결을 위한 작은 코드
- 간단한 예제 코드

이런 경우에 파일을 만들지 않고도 바로 학습할 수 있게 했어요.

## 어떻게 작동하나요?

1. 큰 텍스트 입력 영역(Textarea)에 코드를 붙여넣어요
2. 드롭다운에서 프로그래밍 언어를 선택해요 (JavaScript, Python 등)
3. "코드 추가" 버튼을 클릭하면 코드와 언어 정보가 부모 컴포넌트로 전달돼요
4. 성공하면 입력 영역이 자동으로 비워져요

## TDD로 어떻게 테스트했나요?

- 16개의 테스트 케이스 작성
- Radix UI Select 컴포넌트를 위해 pointer capture mock 필요
- 렌더링, 언어 선택, 코드 입력, 제출 동작 등 테스트

## 관련 파일

- `frontend/src/components/upload/PasteCode.tsx` - 컴포넌트 구현
- `frontend/src/components/upload/PasteCode.test.tsx` - 테스트 코드

## 배운 개념

- **shadcn/ui Select**: Radix UI 기반의 드롭다운 컴포넌트
- **Pointer Capture**: 마우스/터치 이벤트를 특정 요소에 고정하는 API
- **제어 컴포넌트**: React에서 input 상태를 관리하는 패턴

## 주의사항

- Radix UI 컴포넌트는 jsdom에서 `hasPointerCapture` 같은 API가 없어서 mock이 필요해요
- 언어 자동 감지는 백엔드의 역할이에요. 프론트엔드는 사용자가 선택한 언어만 전달해요

## 다음 단계

T079에서 태스크 카드 컴포넌트를 구현할 예정이에요.
