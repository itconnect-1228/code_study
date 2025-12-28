import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { PasteCode } from "./PasteCode";

// Mock pointer capture methods for Radix UI
beforeEach(() => {
  Element.prototype.hasPointerCapture = vi.fn(() => false);
  Element.prototype.setPointerCapture = vi.fn();
  Element.prototype.releasePointerCapture = vi.fn();
});

describe("PasteCode", () => {
  const mockOnPaste = vi.fn();
  const defaultLanguages = ["javascript", "typescript", "python", "java"];

  beforeEach(() => {
    mockOnPaste.mockClear();
  });

  describe("rendering", () => {
    it("renders textarea for code input", () => {
      render(<PasteCode onPaste={mockOnPaste} languages={defaultLanguages} />);
      expect(screen.getByRole("textbox")).toBeInTheDocument();
    });

    it("renders textarea with placeholder", () => {
      render(<PasteCode onPaste={mockOnPaste} languages={defaultLanguages} />);
      expect(
        screen.getByPlaceholderText(/코드를 붙여넣기/i),
      ).toBeInTheDocument();
    });

    it("renders language selector", () => {
      render(<PasteCode onPaste={mockOnPaste} languages={defaultLanguages} />);
      expect(screen.getByRole("combobox")).toBeInTheDocument();
    });

    it("renders submit button", () => {
      render(<PasteCode onPaste={mockOnPaste} languages={defaultLanguages} />);
      expect(
        screen.getByRole("button", { name: /코드 추가/i }),
      ).toBeInTheDocument();
    });
  });

  describe("language selector", () => {
    it("displays default language in trigger", () => {
      render(<PasteCode onPaste={mockOnPaste} languages={defaultLanguages} />);

      const trigger = screen.getByRole("combobox");
      expect(trigger).toHaveTextContent(/javascript/i);
    });

    it("displays custom default language", () => {
      render(
        <PasteCode
          onPaste={mockOnPaste}
          languages={defaultLanguages}
          defaultLanguage="python"
        />,
      );

      const trigger = screen.getByRole("combobox");
      expect(trigger).toHaveTextContent(/python/i);
    });
  });

  describe("code input", () => {
    it("allows typing code in textarea", async () => {
      const user = userEvent.setup();
      render(<PasteCode onPaste={mockOnPaste} languages={defaultLanguages} />);

      const textarea = screen.getByRole("textbox");
      const testCode = 'console.log("Hello, World!");';

      await user.type(textarea, testCode);

      expect(textarea).toHaveValue(testCode);
    });

    it("accepts multiline code via change event", () => {
      render(<PasteCode onPaste={mockOnPaste} languages={defaultLanguages} />);

      const textarea = screen.getByRole("textbox");
      const testCode = 'function hello() {\n  return "world";\n}';

      fireEvent.change(textarea, { target: { value: testCode } });

      expect(textarea).toHaveValue(testCode);
    });
  });

  describe("submit behavior", () => {
    it("calls onPaste with code and default language when submit is clicked", async () => {
      const user = userEvent.setup();
      render(<PasteCode onPaste={mockOnPaste} languages={defaultLanguages} />);

      const textarea = screen.getByRole("textbox");
      const testCode = "const x = 1;";

      await user.type(textarea, testCode);

      const submitButton = screen.getByRole("button", { name: /코드 추가/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnPaste).toHaveBeenCalledWith({
          code: testCode,
          language: "javascript",
        });
      });
    });

    it("disables submit button when code is empty", () => {
      render(<PasteCode onPaste={mockOnPaste} languages={defaultLanguages} />);

      const submitButton = screen.getByRole("button", { name: /코드 추가/i });
      expect(submitButton).toBeDisabled();
    });

    it("enables submit button when code is entered", async () => {
      const user = userEvent.setup();
      render(<PasteCode onPaste={mockOnPaste} languages={defaultLanguages} />);

      const textarea = screen.getByRole("textbox");
      await user.type(textarea, "some code");

      const submitButton = screen.getByRole("button", { name: /코드 추가/i });
      expect(submitButton).not.toBeDisabled();
    });

    it("clears textarea after successful submit", async () => {
      const user = userEvent.setup();
      render(<PasteCode onPaste={mockOnPaste} languages={defaultLanguages} />);

      const textarea = screen.getByRole("textbox");
      await user.type(textarea, "const x = 1;");

      const submitButton = screen.getByRole("button", { name: /코드 추가/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(textarea).toHaveValue("");
      });
    });
  });

  describe("disabled state", () => {
    it("disables textarea when disabled prop is true", () => {
      render(
        <PasteCode
          onPaste={mockOnPaste}
          languages={defaultLanguages}
          disabled
        />,
      );
      expect(screen.getByRole("textbox")).toBeDisabled();
    });

    it("disables submit button when disabled prop is true", () => {
      render(
        <PasteCode
          onPaste={mockOnPaste}
          languages={defaultLanguages}
          disabled
        />,
      );
      expect(screen.getByRole("button", { name: /코드 추가/i })).toBeDisabled();
    });
  });

  describe("default language", () => {
    it("uses first language as default when no defaultLanguage provided", () => {
      render(<PasteCode onPaste={mockOnPaste} languages={defaultLanguages} />);

      const trigger = screen.getByRole("combobox");
      expect(trigger).toHaveTextContent(/javascript/i);
    });

    it("uses provided defaultLanguage", () => {
      render(
        <PasteCode
          onPaste={mockOnPaste}
          languages={defaultLanguages}
          defaultLanguage="python"
        />,
      );

      const trigger = screen.getByRole("combobox");
      expect(trigger).toHaveTextContent(/python/i);
    });
  });
});
