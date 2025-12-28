import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { TaskCard, type TaskCardProps } from "./TaskCard";

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe("TaskCard", () => {
  const defaultTask: TaskCardProps["task"] = {
    id: "task-123",
    taskNumber: 1,
    title: "테스트 태스크",
    status: "pending",
    codeLanguage: "javascript",
    uploadType: "file",
    createdAt: "2025-01-15T10:30:00Z",
  };

  const mockOnClick = vi.fn();

  beforeEach(() => {
    mockOnClick.mockClear();
  });

  describe("rendering", () => {
    it("renders task number", () => {
      renderWithRouter(<TaskCard task={defaultTask} />);
      expect(screen.getByText(/Task 1/i)).toBeInTheDocument();
    });

    it("renders task title", () => {
      renderWithRouter(<TaskCard task={defaultTask} />);
      expect(screen.getByText("테스트 태스크")).toBeInTheDocument();
    });

    it("renders code language badge", () => {
      renderWithRouter(<TaskCard task={defaultTask} />);
      expect(screen.getByText(/javascript/i)).toBeInTheDocument();
    });

    it("renders upload type indicator", () => {
      renderWithRouter(<TaskCard task={defaultTask} />);
      expect(screen.getByText(/파일/i)).toBeInTheDocument();
    });

    it("renders formatted creation date", () => {
      renderWithRouter(<TaskCard task={defaultTask} />);
      // Korean date format: 2025년 1월 15일 or similar
      expect(screen.getByText(/2025/)).toBeInTheDocument();
    });
  });

  describe("status indicators", () => {
    it("shows pending status indicator", () => {
      renderWithRouter(<TaskCard task={defaultTask} />);
      expect(screen.getByText(/대기중/i)).toBeInTheDocument();
    });

    it("shows generating status indicator", () => {
      const generatingTask = { ...defaultTask, status: "generating" as const };
      renderWithRouter(<TaskCard task={generatingTask} />);
      expect(screen.getByText(/생성중/i)).toBeInTheDocument();
    });

    it("shows completed status indicator", () => {
      const completedTask = { ...defaultTask, status: "completed" as const };
      renderWithRouter(<TaskCard task={completedTask} />);
      expect(screen.getByText(/완료/i)).toBeInTheDocument();
    });

    it("shows error status indicator", () => {
      const errorTask = { ...defaultTask, status: "error" as const };
      renderWithRouter(<TaskCard task={errorTask} />);
      expect(screen.getByText(/오류/i)).toBeInTheDocument();
    });
  });

  describe("upload type display", () => {
    it("shows file upload type", () => {
      renderWithRouter(<TaskCard task={defaultTask} />);
      expect(screen.getByText(/파일/i)).toBeInTheDocument();
    });

    it("shows folder upload type", () => {
      const folderTask = { ...defaultTask, uploadType: "folder" as const };
      renderWithRouter(<TaskCard task={folderTask} />);
      expect(screen.getByText(/폴더/i)).toBeInTheDocument();
    });

    it("shows paste upload type", () => {
      const pasteTask = { ...defaultTask, uploadType: "paste" as const };
      renderWithRouter(<TaskCard task={pasteTask} />);
      expect(screen.getByText(/붙여넣기/i)).toBeInTheDocument();
    });
  });

  describe("interaction", () => {
    it("calls onClick when card is clicked", async () => {
      const user = userEvent.setup();
      renderWithRouter(<TaskCard task={defaultTask} onClick={mockOnClick} />);

      const card = screen.getByRole("article");
      await user.click(card);

      expect(mockOnClick).toHaveBeenCalledWith(defaultTask);
    });

    it("renders as link when no onClick provided", () => {
      renderWithRouter(<TaskCard task={defaultTask} />);

      const link = screen.getByRole("link");
      expect(link).toHaveAttribute("href", "/tasks/task-123");
    });

    it("does not render link when onClick provided", () => {
      renderWithRouter(<TaskCard task={defaultTask} onClick={mockOnClick} />);

      expect(screen.queryByRole("link")).not.toBeInTheDocument();
    });
  });

  describe("visual styling", () => {
    it("applies hover styles", () => {
      renderWithRouter(<TaskCard task={defaultTask} />);

      const card = screen.getByRole("article");
      expect(card).toHaveClass("hover:shadow-md");
    });

    it("shows completed task with distinct styling", () => {
      const completedTask = { ...defaultTask, status: "completed" as const };
      renderWithRouter(<TaskCard task={completedTask} />);

      const statusBadge = screen.getByText(/완료/i);
      expect(statusBadge).toBeInTheDocument();
    });
  });

  describe("timeline display", () => {
    it("renders with timeline connector when not last item", () => {
      renderWithRouter(<TaskCard task={defaultTask} isLast={false} />);

      const container = screen.getByTestId("task-card-container");
      expect(container).toHaveClass("task-card-with-connector");
    });

    it("does not render timeline connector when last item", () => {
      renderWithRouter(<TaskCard task={defaultTask} isLast={true} />);

      const container = screen.getByTestId("task-card-container");
      expect(container).not.toHaveClass("task-card-with-connector");
    });
  });
});
