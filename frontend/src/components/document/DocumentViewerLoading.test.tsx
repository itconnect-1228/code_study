import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { DocumentViewerLoading } from "./DocumentViewerLoading";

describe("DocumentViewerLoading", () => {
  describe("상태별 렌더링", () => {
    it("pending 상태일 때 대기 메시지를 표시해야 함", () => {
      render(<DocumentViewerLoading status="pending" />);

      expect(screen.getByText(/문서 생성 대기 중/i)).toBeInTheDocument();
    });

    it("generating 상태일 때 생성 중 메시지를 표시해야 함", () => {
      render(<DocumentViewerLoading status="generating" />);

      expect(screen.getByText(/문서 생성 중/i)).toBeInTheDocument();
    });

    it("error 상태일 때 오류 메시지를 표시해야 함", () => {
      render(<DocumentViewerLoading status="error" />);

      expect(screen.getByText(/오류가 발생했습니다/i)).toBeInTheDocument();
    });
  });

  describe("진행률 표시", () => {
    it("진행률이 제공되면 Progress 컴포넌트가 표시되어야 함", () => {
      render(<DocumentViewerLoading status="generating" progress={50} />);

      expect(screen.getByRole("progressbar")).toBeInTheDocument();
    });

    it("진행률 값이 표시되어야 함", () => {
      render(<DocumentViewerLoading status="generating" progress={75} />);

      expect(screen.getByText(/75%/)).toBeInTheDocument();
    });

    it("진행률이 없으면 불확정 로딩 표시해야 함", () => {
      render(<DocumentViewerLoading status="generating" />);

      // 스피너나 불확정 로딩 표시
      expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
    });
  });

  describe("에러 처리", () => {
    it("에러 메시지가 제공되면 표시해야 함", () => {
      render(
        <DocumentViewerLoading status="error" errorMessage="API 연결 실패" />,
      );

      expect(screen.getByText(/API 연결 실패/)).toBeInTheDocument();
    });

    it("재시도 버튼이 표시되어야 함", () => {
      const onRetry = vi.fn();
      render(<DocumentViewerLoading status="error" onRetry={onRetry} />);

      expect(
        screen.getByRole("button", { name: /다시 시도/i }),
      ).toBeInTheDocument();
    });

    it("재시도 버튼 클릭 시 onRetry 콜백이 호출되어야 함", async () => {
      const { userEvent } = await import("@testing-library/user-event");
      const user = userEvent.setup();
      const onRetry = vi.fn();
      render(<DocumentViewerLoading status="error" onRetry={onRetry} />);

      await user.click(screen.getByRole("button", { name: /다시 시도/i }));

      expect(onRetry).toHaveBeenCalled();
    });
  });

  describe("문서 생성 요청", () => {
    it("pending 상태에서 생성 시작 버튼이 표시되어야 함", () => {
      render(<DocumentViewerLoading status="pending" onGenerate={vi.fn()} />);

      expect(
        screen.getByRole("button", { name: /문서 생성/i }),
      ).toBeInTheDocument();
    });

    it("생성 버튼 클릭 시 onGenerate 콜백이 호출되어야 함", async () => {
      const { userEvent } = await import("@testing-library/user-event");
      const user = userEvent.setup();
      const onGenerate = vi.fn();
      render(
        <DocumentViewerLoading status="pending" onGenerate={onGenerate} />,
      );

      await user.click(screen.getByRole("button", { name: /문서 생성/i }));

      expect(onGenerate).toHaveBeenCalled();
    });
  });

  describe("스타일링", () => {
    it("컨테이너에 기본 클래스가 적용되어야 함", () => {
      const { container } = render(<DocumentViewerLoading status="pending" />);

      const wrapper = container.firstChild;
      expect(wrapper).toHaveClass("document-viewer-loading");
    });

    it("커스텀 className을 적용할 수 있어야 함", () => {
      const { container } = render(
        <DocumentViewerLoading status="pending" className="custom-class" />,
      );

      const wrapper = container.firstChild;
      expect(wrapper).toHaveClass("custom-class");
    });
  });
});
