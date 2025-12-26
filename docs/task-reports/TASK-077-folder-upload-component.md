# T077: FolderUpload 컴포넌트

## 무엇을 만들었나요?

폴더 전체를 업로드할 수 있는 React 컴포넌트를 만들었어요. 개별 파일이 아닌 프로젝트 폴더 전체를 한 번에 올릴 수 있어서, 여러 파일로 구성된 프로젝트를 학습할 때 편리해요.

## 왜 이렇게 만들었나요?

실제 코드 프로젝트는 보통 여러 파일과 폴더로 구성되어 있어요. 예를 들어 React 프로젝트라면 `src/`, `components/`, `pages/` 등 폴더 구조가 있죠. 이런 구조를 그대로 보존하면서 업로드하면, 나중에 학습 문서를 생성할 때 파일 간의 관계를 더 잘 이해할 수 있어요.

## 어떻게 작동하나요?

1. HTML5의 `webkitdirectory` 속성을 사용해서 폴더 선택을 지원해요
2. 각 파일에는 `webkitRelativePath`라는 속성이 있어서 원래 폴더 경로를 알 수 있어요
3. 폴더 내 파일 개수가 너무 많으면 에러를 표시해요 (서버 부하 방지)

## TDD로 어떻게 테스트했나요?

- 12개의 테스트 케이스 작성
- jsdom에서 `FileList`를 mock하는 헬퍼 함수 구현
- 폴더 선택, 드래그 앤 드롭, 파일 개수 검증, 비활성화 상태 등 테스트

## 관련 파일

- `frontend/src/components/upload/FolderUpload.tsx` - 컴포넌트 구현
- `frontend/src/components/upload/FolderUpload.test.tsx` - 테스트 코드

## 배운 개념

- **webkitdirectory**: 폴더 선택을 위한 HTML input 속성
- **webkitRelativePath**: 선택된 파일의 상대 경로
- **FileList Mock**: 테스트 환경에서 FileList를 흉내내는 방법

## 주의사항

- `webkitdirectory`는 Webkit 기반 브라우저(Chrome, Safari)에서 지원돼요. Firefox도 지원하지만 완벽하지 않을 수 있어요
- 폴더 업로드는 보안상의 이유로 드래그 앤 드롭으로는 완벽하게 작동하지 않을 수 있어요

## 다음 단계

T078에서 코드 붙여넣기 기능을 구현할 예정이에요.
