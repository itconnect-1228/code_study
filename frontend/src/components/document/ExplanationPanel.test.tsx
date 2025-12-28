import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ExplanationPanel } from "./ExplanationPanel";
import type { LearningDocument } from "@/services/document-service";

// 샘플 학습 문서 데이터
const sampleDocument: LearningDocument = {
  id: "doc-123",
  taskId: "task-456",
  status: "completed",
  chapters: {
    summary: {
      title: "코드 요약",
      content: "이 코드는 간단한 Hello World 프로그램입니다.",
    },
    prerequisites: {
      title: "사전 지식",
      concepts: [
        {
          name: "함수",
          explanation: "재사용 가능한 코드 블록입니다.",
          analogy:
            "레시피와 같습니다. 한 번 정의하면 여러 번 사용할 수 있습니다.",
        },
        {
          name: "변수",
          explanation: "데이터를 저장하는 컨테이너입니다.",
          analogy: "라벨이 붙은 상자와 같습니다.",
        },
      ],
    },
    coreLogic: {
      title: "핵심 로직",
      content: "함수를 정의하고 호출하는 기본 패턴을 보여줍니다.",
    },
    lineByLine: {
      title: "라인별 설명",
      explanations: [
        {
          lineNumber: 1,
          code: "function hello() {",
          explanation: "함수를 선언합니다.",
        },
        {
          lineNumber: 2,
          code: 'console.log("Hello!");',
          explanation: "콘솔에 메시지를 출력합니다.",
        },
        { lineNumber: 3, code: "}", explanation: "함수 블록을 종료합니다." },
      ],
    },
    syntaxReference: {
      title: "문법 레퍼런스",
      items: [
        { syntax: "function", description: "함수를 정의하는 키워드" },
        { syntax: "console.log", description: "콘솔에 출력하는 메서드" },
      ],
    },
    commonPatterns: {
      title: "자주 쓰는 패턴",
      patterns: [
        {
          name: "함수 정의 패턴",
          description: "함수를 정의하고 호출하는 기본 패턴",
        },
      ],
    },
    exercises: {
      title: "연습 문제",
      items: [
        {
          question: "다른 메시지를 출력하는 함수를 만들어보세요.",
          hint: "console.log 내용을 변경하세요.",
        },
      ],
    },
  },
  createdAt: "2025-01-01T00:00:00Z",
  updatedAt: "2025-01-01T00:00:00Z",
};

describe("ExplanationPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("렌더링", () => {
    it("7개의 챕터 네비게이션 탭이 렌더링되어야 함", () => {
      render(<ExplanationPanel document={sampleDocument} />);

      expect(screen.getByRole("tab", { name: /요약/i })).toBeInTheDocument();
      expect(
        screen.getByRole("tab", { name: /사전 지식/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("tab", { name: /핵심 로직/i }),
      ).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /라인별/i })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /문법/i })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /패턴/i })).toBeInTheDocument();
      expect(screen.getByRole("tab", { name: /연습/i })).toBeInTheDocument();
    });

    it("기본적으로 첫 번째 챕터(요약)가 선택되어야 함", () => {
      render(<ExplanationPanel document={sampleDocument} />);

      const summaryTab = screen.getByRole("tab", { name: /요약/i });
      expect(summaryTab).toHaveAttribute("data-active", "true");
    });

    it("첫 번째 챕터의 콘텐츠가 표시되어야 함", () => {
      render(<ExplanationPanel document={sampleDocument} />);

      expect(
        screen.getByText(/이 코드는 간단한 Hello World 프로그램입니다/),
      ).toBeInTheDocument();
    });
  });

  describe("챕터 네비게이션", () => {
    it("다른 챕터를 클릭하면 해당 챕터로 이동해야 함", async () => {
      const user = userEvent.setup();
      render(<ExplanationPanel document={sampleDocument} />);

      const prereqTab = screen.getByRole("tab", { name: /사전 지식/i });
      await user.click(prereqTab);

      expect(prereqTab).toHaveAttribute("data-active", "true");
    });

    it("챕터 변경 시 해당 챕터의 콘텐츠가 표시되어야 함", async () => {
      const user = userEvent.setup();
      render(<ExplanationPanel document={sampleDocument} />);

      await user.click(screen.getByRole("tab", { name: /사전 지식/i }));

      // 사전 지식 챕터의 개념 카드가 표시되어야 함
      expect(screen.getByText("함수")).toBeInTheDocument();
    });

    it("onChapterChange 콜백이 호출되어야 함", async () => {
      const user = userEvent.setup();
      const onChapterChange = vi.fn();
      render(
        <ExplanationPanel
          document={sampleDocument}
          onChapterChange={onChapterChange}
        />,
      );

      await user.click(screen.getByRole("tab", { name: /라인별/i }));

      expect(onChapterChange).toHaveBeenCalledWith("lineByLine");
    });
  });

  describe("현재 챕터 하이라이트", () => {
    it("현재 선택된 챕터가 시각적으로 구분되어야 함", () => {
      render(
        <ExplanationPanel
          document={sampleDocument}
          currentChapter="prerequisites"
        />,
      );

      const prereqTab = screen.getByRole("tab", { name: /사전 지식/i });
      expect(prereqTab).toHaveAttribute("data-active", "true");
    });

    it("선택되지 않은 챕터는 비활성 상태여야 함", () => {
      render(
        <ExplanationPanel document={sampleDocument} currentChapter="summary" />,
      );

      const prereqTab = screen.getByRole("tab", { name: /사전 지식/i });
      expect(prereqTab).toHaveAttribute("data-active", "false");
    });
  });

  describe("스타일링", () => {
    it("컨테이너에 기본 클래스가 적용되어야 함", () => {
      const { container } = render(
        <ExplanationPanel document={sampleDocument} />,
      );

      const panel = container.firstChild;
      expect(panel).toHaveClass("explanation-panel");
    });

    it("커스텀 className을 적용할 수 있어야 함", () => {
      const { container } = render(
        <ExplanationPanel document={sampleDocument} className="custom-class" />,
      );

      const panel = container.firstChild;
      expect(panel).toHaveClass("custom-class");
    });
  });

  describe("접근성", () => {
    it("네비게이션 탭이 키보드로 접근 가능해야 함", async () => {
      const user = userEvent.setup();
      render(<ExplanationPanel document={sampleDocument} />);

      const summaryTab = screen.getByRole("tab", { name: /요약/i });
      await user.tab();

      expect(summaryTab).toHaveFocus();
    });
  });
});
