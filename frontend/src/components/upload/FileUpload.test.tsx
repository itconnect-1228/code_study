import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { FileUpload } from "./FileUpload";

describe("FileUpload", () => {
  const mockOnFileSelect = vi.fn();

  beforeEach(() => {
    mockOnFileSelect.mockClear();
  });

  describe("rendering", () => {
    it("renders file upload area", () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} />);
      expect(screen.getByText(/파일을 드래그/i)).toBeInTheDocument();
    });

    it("renders file picker button", () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} />);
      expect(
        screen.getByRole("button", { name: /파일 선택/i }),
      ).toBeInTheDocument();
    });

    it("renders hidden file input", () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} />);
      const fileInput = document.querySelector('input[type="file"]');
      expect(fileInput).toBeInTheDocument();
    });
  });

  describe("file picker", () => {
    it("opens file picker when button is clicked", async () => {
      const user = userEvent.setup();
      render(<FileUpload onFileSelect={mockOnFileSelect} />);
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      const clickSpy = vi.spyOn(fileInput, "click");
      const button = screen.getByRole("button", { name: /파일 선택/i });
      await user.click(button);
      expect(clickSpy).toHaveBeenCalled();
    });

    it("calls onFileSelect when file is selected", async () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} />);
      const file = new File(["test content"], "test.ts", {
        type: "text/typescript",
      });
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      fireEvent.change(fileInput, { target: { files: [file] } });
      await waitFor(() => {
        expect(mockOnFileSelect).toHaveBeenCalledWith([file]);
      });
    });

    it("supports multiple file selection", async () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} />);
      const file1 = new File(["content1"], "test1.ts", {
        type: "text/typescript",
      });
      const file2 = new File(["content2"], "test2.ts", {
        type: "text/typescript",
      });
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      fireEvent.change(fileInput, { target: { files: [file1, file2] } });
      await waitFor(() => {
        expect(mockOnFileSelect).toHaveBeenCalledWith([file1, file2]);
      });
    });
  });

  describe("drag and drop", () => {
    it("shows drag-over state when file is dragged over", () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} />);
      const dropZone = screen.getByTestId("file-drop-zone");
      fireEvent.dragEnter(dropZone, { dataTransfer: { types: ["Files"] } });
      expect(dropZone).toHaveClass("border-primary");
    });

    it("removes drag-over state when file leaves", () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} />);
      const dropZone = screen.getByTestId("file-drop-zone");
      fireEvent.dragEnter(dropZone, { dataTransfer: { types: ["Files"] } });
      fireEvent.dragLeave(dropZone);
      expect(dropZone).not.toHaveClass("border-primary");
    });

    it("calls onFileSelect when files are dropped", async () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} />);
      const file = new File(["test content"], "test.ts", {
        type: "text/typescript",
      });
      const dropZone = screen.getByTestId("file-drop-zone");
      fireEvent.drop(dropZone, {
        dataTransfer: { files: [file], types: ["Files"] },
      });
      await waitFor(() => {
        expect(mockOnFileSelect).toHaveBeenCalledWith([file]);
      });
    });
  });

  describe("file type filtering", () => {
    it("accepts files with allowed types", async () => {
      render(
        <FileUpload
          onFileSelect={mockOnFileSelect}
          acceptedTypes={[".ts", ".tsx", ".js", ".jsx"]}
        />,
      );
      const file = new File(["content"], "test.ts", {
        type: "text/typescript",
      });
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      fireEvent.change(fileInput, { target: { files: [file] } });
      await waitFor(() => {
        expect(mockOnFileSelect).toHaveBeenCalledWith([file]);
      });
    });

    it("sets accept attribute on file input", () => {
      render(
        <FileUpload
          onFileSelect={mockOnFileSelect}
          acceptedTypes={[".ts", ".tsx"]}
        />,
      );
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      expect(fileInput.accept).toBe(".ts,.tsx");
    });
  });

  describe("file size validation", () => {
    it("rejects files exceeding maxSize", async () => {
      const onError = vi.fn();
      render(
        <FileUpload
          onFileSelect={mockOnFileSelect}
          maxSize={1024}
          onError={onError}
        />,
      );
      const largeContent = "x".repeat(2048);
      const file = new File([largeContent], "large.ts", {
        type: "text/typescript",
      });
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      fireEvent.change(fileInput, { target: { files: [file] } });
      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith(expect.stringContaining("크기"));
        expect(mockOnFileSelect).not.toHaveBeenCalled();
      });
    });

    it("accepts files within maxSize", async () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} maxSize={1024} />);
      const file = new File(["small"], "small.ts", { type: "text/typescript" });
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      fireEvent.change(fileInput, { target: { files: [file] } });
      await waitFor(() => {
        expect(mockOnFileSelect).toHaveBeenCalledWith([file]);
      });
    });
  });

  describe("disabled state", () => {
    it("disables file selection when disabled prop is true", () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} disabled />);
      const button = screen.getByRole("button", { name: /파일 선택/i });
      expect(button).toBeDisabled();
    });

    it("ignores drag and drop when disabled", async () => {
      render(<FileUpload onFileSelect={mockOnFileSelect} disabled />);
      const file = new File(["test content"], "test.ts", {
        type: "text/typescript",
      });
      const dropZone = screen.getByTestId("file-drop-zone");
      fireEvent.drop(dropZone, {
        dataTransfer: { files: [file], types: ["Files"] },
      });
      await waitFor(() => {
        expect(mockOnFileSelect).not.toHaveBeenCalled();
      });
    });
  });
});
