import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { DocumentViewer } from "./DocumentViewer";
import type { LearningDocument } from "@/services/document-service";
import type { CodeFile } from "@/services/task-service";

// Monaco Editor 모킹
vi.mock("@monaco-editor/react", () => ({
  default: vi.fn(({ value, language }) => (
    <div data-testid="monaco-editor" data-language={language}>
      {value}
    </div>
  )),
}));

describe("DocumentViewer", () => {
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
            analogy: "레시피와 같습니다.",
          },
        ],
      },
      coreLogic: {
        title: "핵심 로직",
        content: "함수를 정의하고 호출하는 패턴입니다.",
      },
      lineByLine: {
        title: "라인별 설명",
        explanations: [
          {
            lineNumber: 1,
            code: "function hello() {",
            explanation: "함수 선언",
          },
          { lineNumber: 2, code: 'console.log("Hello");', explanation: "출력" },
        ],
      },
      syntaxReference: {
        title: "문법 레퍼런스",
        items: [{ syntax: "function", description: "함수 정의 키워드" }],
      },
      commonPatterns: {
        title: "자주 쓰는 패턴",
        patterns: [{ name: "함수 패턴", description: "함수 정의 및 호출" }],
      },
      exercises: {
        title: "연습 문제",
        items: [
          { question: "다른 메시지를 출력하세요.", hint: "console.log 사용" },
        ],
      },
    },
    createdAt: "2025-01-01T00:00:00Z",
    updatedAt: "2025-01-01T00:00:00Z",
  };

  const sampleCodeFile: CodeFile = {
    id: "file-1",
    filename: "hello.js",
    relativePath: "hello.js",
    content: 'function hello() {\n  console.log("Hello");\n}\n\nhello();',
    language: "javascript",
    lineCount: 5,
    sizeBytes: 50,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("2단 레이아웃", () => {
    it("CodePanel과 ExplanationPanel이 나란히 렌더링되어야 함", () => {
      render(
        <DocumentViewer document={sampleDocument} codeFile={sampleCodeFile} />,
      );

      expect(screen.getByTestId("code-panel")).toBeInTheDocument();
      expect(screen.getByTestId("explanation-panel")).toBeInTheDocument();
    });

    it("Monaco Editor가 코드를 표시해야 함", () => {
      render(
        <DocumentViewer document={sampleDocument} codeFile={sampleCodeFile} />,
      );

      expect(screen.getByTestId("monaco-editor")).toHaveTextContent(
        "function hello()",
      );
    });

    it("ExplanationPanel이 문서 내용을 표시해야 함", () => {
      render(
        <DocumentViewer document={sampleDocument} codeFile={sampleCodeFile} />,
      );

      expect(screen.getByText(/Hello World 프로그램/)).toBeInTheDocument();
    });
  });

  describe("챕터 네비게이션", () => {
    it("챕터 탭을 클릭하면 해당 챕터로 이동해야 함", async () => {
      const user = userEvent.setup();
      render(
        <DocumentViewer document={sampleDocument} codeFile={sampleCodeFile} />,
      );

      await user.click(screen.getByRole("tab", { name: /사전 지식/i }));

      expect(screen.getByText("함수")).toBeInTheDocument();
    });
  });

  describe("라인 동기화", () => {
    it("라인별 설명에서 라인을 선택하면 onLineSelect가 호출되어야 함", async () => {
      const user = userEvent.setup();
      const onLineSelect = vi.fn();
      render(
        <DocumentViewer
          document={sampleDocument}
          codeFile={sampleCodeFile}
          onLineSelect={onLineSelect}
        />,
      );

      // 라인별 설명 챕터로 이동
      await user.click(screen.getByRole("tab", { name: /라인별/i }));

      // 라인 선택
      const lineItem = screen.getByTestId("line-item-1");
      await user.click(lineItem);

      expect(onLineSelect).toHaveBeenCalledWith(1);
    });
  });

  describe("스타일링", () => {
    it("컨테이너에 기본 클래스가 적용되어야 함", () => {
      const { container } = render(
        <DocumentViewer document={sampleDocument} codeFile={sampleCodeFile} />,
      );

      const viewer = container.firstChild;
      expect(viewer).toHaveClass("document-viewer");
    });

    it("커스텀 className을 적용할 수 있어야 함", () => {
      const { container } = render(
        <DocumentViewer
          document={sampleDocument}
          codeFile={sampleCodeFile}
          className="custom-class"
        />,
      );

      const viewer = container.firstChild;
      expect(viewer).toHaveClass("custom-class");
    });
  });

  describe("반응형 레이아웃", () => {
    it("2단 그리드 레이아웃이 적용되어야 함", () => {
      const { container } = render(
        <DocumentViewer document={sampleDocument} codeFile={sampleCodeFile} />,
      );

      const layout = container.querySelector(".document-viewer-layout");
      expect(layout).toHaveClass("grid");
    });
  });

  describe("코드 파일 없음 처리", () => {
    it("코드 파일이 없을 때 메시지를 표시해야 함", () => {
      render(<DocumentViewer document={sampleDocument} />);

      expect(screen.getByText(/코드 파일이 없습니다/i)).toBeInTheDocument();
    });
  });
});
