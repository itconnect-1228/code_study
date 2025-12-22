# Task 022: Tailwind CSS 및 shadcn/ui 컴포넌트 설정

**완료일**: 2025-12-22
**관련 파일**: frontend/vite.config.ts, frontend/src/index.css, frontend/components.json, frontend/src/components/ui/*, frontend/src/lib/utils.ts

## 무엇을 만들었나요?

프론트엔드 프로젝트에 Tailwind CSS v4와 shadcn/ui 컴포넌트 라이브러리를 설정했습니다. 마치 집을 지을 때 표준화된 건축 자재(Tailwind CSS)와 미리 만들어진 문, 창문(shadcn/ui)을 준비하는 것과 같습니다.

## 왜 이렇게 만들었나요?

웹 애플리케이션을 만들 때 일관된 디자인과 사용자 경험을 제공하려면 체계적인 UI 시스템이 필요합니다:

- **Tailwind CSS v4**: 최신 버전을 사용하여 CSS 변수 기반 테마, 빠른 빌드, 더 작은 번들 크기를 얻었습니다
- **shadcn/ui**: 복사-붙여넣기 방식의 컴포넌트로 코드를 직접 수정할 수 있고, 필요한 컴포넌트만 포함하여 번들 크기를 최소화합니다

## 어떻게 작동하나요?

### 1. Tailwind CSS v4 설정
Tailwind v4는 Vite 플러그인을 통해 통합됩니다:
```typescript
// vite.config.ts
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

### 2. CSS 변수 기반 테마
라이트/다크 모드를 자동으로 지원하는 oklch 색상 시스템:
```css
:root {
  --primary: oklch(0.205 0 0);
  --background: oklch(1 0 0);
}
.dark {
  --primary: oklch(0.985 0 0);
  --background: oklch(0.145 0 0);
}
```

### 3. 컴포넌트 사용
```typescript
import { Button } from "@/components/ui/button"
<Button variant="default">클릭하세요</Button>
```

### 4. cn() 유틸리티
클래스명 병합과 충돌 해결:
```typescript
cn("text-base", "text-lg")  // "text-lg"만 적용
```

## 테스트는 어떻게 했나요?

인프라 설정 작업이므로 TDD 사이클은 적용되지 않습니다:
- `npm run build` 실행하여 TypeScript 컴파일 및 Vite 빌드 성공 확인
- 모든 14개 UI 컴포넌트가 정상적으로 설치되었는지 확인

## 수정된 파일

### 생성된 파일 (17개)
- `frontend/components.json`: shadcn/ui 설정 파일
- `frontend/src/lib/utils.ts`: cn() 유틸리티 함수
- `frontend/src/components/ui/*.tsx`: 14개 UI 컴포넌트
  - button, input, label, textarea, select (폼 요소)
  - card, dialog, separator, skeleton (레이아웃)
  - badge, progress, sonner (피드백)
  - dropdown-menu, avatar (네비게이션)

### 수정된 파일 (4개)
- `frontend/package.json`: 의존성 추가
- `frontend/vite.config.ts`: Tailwind 플러그인 및 경로 별칭 설정
- `frontend/tsconfig.app.json`: 경로 별칭 설정
- `frontend/src/index.css`: Tailwind v4 CSS 변수 및 테마 설정

## 관련 개념

### Tailwind CSS v4
기존 v3과 달리 JavaScript 설정 파일 대신 CSS 내에서 `@theme inline` 지시어로 테마를 설정합니다. 빌드 속도가 빠르고 번들 크기가 더 작습니다.

### oklch 색상
사람의 인지에 더 가까운 색상 모델로, Lightness(밝기), Chroma(채도), Hue(색상)를 독립적으로 조절할 수 있습니다.

### 경로 별칭 (@/)
`import { Button } from "../../../components/ui/button"` 대신
`import { Button } from "@/components/ui/button"`로 간결하게 작성할 수 있습니다.

## 주의사항

1. **Tailwind v4 호환성**: shadcn/ui CLI가 생성하는 컴포넌트가 일부 수정이 필요할 수 있습니다 (예: sonner.tsx의 next-themes 의존성 제거)
2. **경로 별칭**: vite.config.ts와 tsconfig.app.json 모두에 설정해야 합니다
3. **"use client" 지시어**: Next.js용 지시어이지만 Vite에서는 무시되므로 제거하지 않아도 됩니다

## 다음 단계

Phase 2 (Foundational)이 완료되었습니다!

**다음 Phase**: Phase 3 - Authentication Slice (인증 시스템)

다음 작업들에서 이 컴포넌트들을 사용하게 됩니다:
- T032: 회원가입 폼 (Button, Input, Label 사용)
- T033: 로그인 폼 (Button, Input, Label 사용)
- T051: 프로젝트 카드 (Card 사용)
- T052: 프로젝트 생성 모달 (Dialog 사용)
