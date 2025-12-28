import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { CodePanel } from "./CodePanel";

// Monaco Editor 모킹
vi.mock("@monaco-editor/react", () => ({
  default: vi.fn(({ value, language, options }) => (
    <div
      data-testid="monaco-editor"
      data-language={language}
      data-readonly={options?.readOnly}
    >
      {value}
    </div>
  )),
}));

describe("CodePanel", () => {
  const sampleCode = `function hello() {
  console.log("Hello, World!");
}

hello();`;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("렌더링", () => {
    it("Monaco Editor가 렌더링되어야 함", async () => {
      render(<CodePanel code={sampleCode} language="javascript" />);

      await waitFor(() => {
        expect(screen.getByTestId("monaco-editor")).toBeInTheDocument();
      });
    });

    it("코드가 올바르게 표시되어야 함", async () => {
      render(<CodePanel code={sampleCode} language="javascript" />);

      await waitFor(() => {
        expect(screen.getByTestId("monaco-editor")).toHaveTextContent(
          "function hello()",
        );
      });
    });

    it("언어가 올바르게 설정되어야 함", async () => {
      render(<CodePanel code={sampleCode} language="javascript" />);

      await waitFor(() => {
        expect(screen.getByTestId("monaco-editor")).toHaveAttribute(
          "data-language",
          "javascript",
        );
      });
    });

    it("읽기 전용 모드로 설정되어야 함", async () => {
      render(<CodePanel code={sampleCode} language="javascript" />);

      await waitFor(() => {
        expect(screen.getByTestId("monaco-editor")).toHaveAttribute(
          "data-readonly",
          "true",
        );
      });
    });
  });

  describe("다양한 언어 지원", () => {
    it("Python 코드를 표시할 수 있어야 함", async () => {
      const pythonCode = 'print("Hello, Python!")';
      render(<CodePanel code={pythonCode} language="python" />);

      await waitFor(() => {
        expect(screen.getByTestId("monaco-editor")).toHaveAttribute(
          "data-language",
          "python",
        );
      });
    });

    it("TypeScript 코드를 표시할 수 있어야 함", async () => {
      const tsCode = 'const greeting: string = "Hello";';
      render(<CodePanel code={tsCode} language="typescript" />);

      await waitFor(() => {
        expect(screen.getByTestId("monaco-editor")).toHaveAttribute(
          "data-language",
          "typescript",
        );
      });
    });
  });

  describe("스타일링", () => {
    it("컨테이너에 기본 클래스가 적용되어야 함", () => {
      const { container } = render(
        <CodePanel code={sampleCode} language="javascript" />,
      );

      const panel = container.firstChild;
      expect(panel).toHaveClass("code-panel");
    });

    it("커스텀 className을 적용할 수 있어야 함", () => {
      const { container } = render(
        <CodePanel
          code={sampleCode}
          language="javascript"
          className="custom-class"
        />,
      );

      const panel = container.firstChild;
      expect(panel).toHaveClass("custom-class");
    });
  });

  describe("빈 코드 처리", () => {
    it("빈 코드를 처리할 수 있어야 함", async () => {
      render(<CodePanel code="" language="javascript" />);

      await waitFor(() => {
        expect(screen.getByTestId("monaco-editor")).toBeInTheDocument();
      });
    });
  });

  describe("하이라이트 기능", () => {
    it("특정 라인을 하이라이트할 수 있어야 함", async () => {
      render(
        <CodePanel
          code={sampleCode}
          language="javascript"
          highlightedLines={[1, 2]}
        />,
      );

      await waitFor(() => {
        expect(screen.getByTestId("monaco-editor")).toBeInTheDocument();
      });
    });
  });

  describe("파일 정보 표시", () => {
    it("파일명이 제공되면 헤더에 표시되어야 함", () => {
      render(
        <CodePanel
          code={sampleCode}
          language="javascript"
          filename="example.js"
        />,
      );

      expect(screen.getByText("example.js")).toBeInTheDocument();
    });

    it("파일명이 없으면 헤더가 표시되지 않아야 함", () => {
      render(<CodePanel code={sampleCode} language="javascript" />);

      expect(screen.queryByTestId("code-panel-header")).not.toBeInTheDocument();
    });
  });
});
