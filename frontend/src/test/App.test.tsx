import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "../App";

// Mock the services
vi.mock("@/services/project-service", () => ({
  projectService: {
    getProjects: vi.fn().mockResolvedValue({ projects: [], total: 0 }),
    getProject: vi.fn().mockResolvedValue({
      id: "123",
      title: "Test Project",
      description: "Test Description",
      createdAt: "2025-01-15T10:00:00Z",
      lastActivityAt: "2025-01-15T10:00:00Z",
      taskCount: 0,
    }),
  },
}));

vi.mock("@/services/task-service", () => ({
  taskService: {
    getTasks: vi.fn().mockResolvedValue({ tasks: [], total: 0 }),
    getTask: vi.fn().mockResolvedValue({
      id: "456",
      taskNumber: 1,
      title: "Test Task",
      status: "completed",
      codeLanguage: "javascript",
      createdAt: "2025-01-15T10:00:00Z",
      updatedAt: "2025-01-15T10:00:00Z",
    }),
    getTaskCode: vi.fn().mockResolvedValue({ files: [], total: 0 }),
  },
}));

// Mock auth store - support selector pattern
const mockAuthState = {
  user: { id: "1", email: "test@example.com" },
  isAuthenticated: true,
  isLoading: false,
  setUser: vi.fn(),
  setLoading: vi.fn(),
  clearAuth: vi.fn(),
};

vi.mock("@/stores/auth-store", () => ({
  useAuthStore: (selector?: (state: typeof mockAuthState) => unknown) => {
    if (selector) {
      return selector(mockAuthState);
    }
    return mockAuthState;
  },
}));

// Mock pointer capture for Radix UI
beforeEach(() => {
  Element.prototype.hasPointerCapture = vi.fn(() => false);
  Element.prototype.setPointerCapture = vi.fn();
  Element.prototype.releasePointerCapture = vi.fn();
});

const createQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const renderWithRouter = (initialRoute: string) => {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("App Router", () => {
  it("renders Dashboard at /", async () => {
    renderWithRouter("/");

    await waitFor(() => {
      // Dashboard shows "내 프로젝트" heading
      expect(
        screen.getByRole("heading", { name: /내 프로젝트/i }),
      ).toBeInTheDocument();
    });
  });

  it("renders Register page at /register", () => {
    renderWithRouter("/register");
    expect(screen.getByText(/create account/i)).toBeInTheDocument();
  });

  it("renders Login page at /login", () => {
    renderWithRouter("/login");
    expect(screen.getByText(/welcome back/i)).toBeInTheDocument();
  });

  it("renders ProjectDetail page at /projects/:id", async () => {
    renderWithRouter("/projects/123");

    await waitFor(() => {
      // ProjectDetail shows project title
      expect(screen.getByText("Test Project")).toBeInTheDocument();
    });
  });

  it("renders TaskDetail page at /tasks/:id", async () => {
    renderWithRouter("/tasks/456");

    await waitFor(() => {
      // TaskDetail shows task title
      expect(screen.getByText("Test Task")).toBeInTheDocument();
    });
  });

  it("renders Trash page at /trash", async () => {
    renderWithRouter("/trash");

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /휴지통/i }),
      ).toBeInTheDocument();
    });
  });

  it("renders NotFound page for unknown routes", () => {
    renderWithRouter("/unknown-route");
    expect(screen.getByRole("heading", { name: /404/i })).toBeInTheDocument();
  });

  it("NotFound page has link to dashboard", () => {
    renderWithRouter("/unknown-route");
    expect(
      screen.getByRole("link", { name: /대시보드로 돌아가기/i }),
    ).toHaveAttribute("href", "/");
  });
});
