import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import Register from "../Register";
import { authService } from "@/services/auth-service";
import { useAuthStore } from "@/stores/auth-store";

// Mock the auth service
vi.mock("@/services/auth-service", () => ({
  authService: {
    register: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("Register Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset auth store
    useAuthStore.getState().clearAuth();
  });

  it("renders the register form", () => {
    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>,
    );

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /register|sign up/i }),
    ).toBeInTheDocument();
  });

  it("renders page title", () => {
    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>,
    );

    expect(screen.getByText(/create account/i)).toBeInTheDocument();
  });

  it("renders link to login page", () => {
    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("link", { name: /login|sign in/i }),
    ).toBeInTheDocument();
  });

  it("calls register service, updates auth store, and navigates to dashboard on success", async () => {
    const user = userEvent.setup();
    vi.mocked(authService.register).mockResolvedValue({
      id: "123",
      email: "test@example.com",
      skillLevel: "beginner",
    } as never);

    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "password123");
    await user.type(screen.getByLabelText(/confirm password/i), "password123");
    await user.click(screen.getByRole("button", { name: /register|sign up/i }));

    await waitFor(() => {
      expect(authService.register).toHaveBeenCalledWith(
        "test@example.com",
        "password123",
      );
    });

    // Should update auth store with user data (auto-login)
    await waitFor(() => {
      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.user).not.toBeNull();
      expect(state.user?.email).toBe("test@example.com");
    });

    // Should navigate to dashboard instead of login
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/");
    });
  });

  it("displays error message on registration failure", async () => {
    const user = userEvent.setup();
    vi.mocked(authService.register).mockRejectedValue({
      response: { data: { detail: "Email already registered" } },
    });

    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "password123");
    await user.type(screen.getByLabelText(/confirm password/i), "password123");
    await user.click(screen.getByRole("button", { name: /register|sign up/i }));

    await waitFor(() => {
      expect(screen.getByText(/email already registered/i)).toBeInTheDocument();
    });
  });

  it("shows loading state while registering", async () => {
    const user = userEvent.setup();
    vi.mocked(authService.register).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100)),
    );

    render(
      <MemoryRouter>
        <Register />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText(/email/i), "test@example.com");
    await user.type(screen.getByLabelText(/^password$/i), "password123");
    await user.type(screen.getByLabelText(/confirm password/i), "password123");
    await user.click(screen.getByRole("button", { name: /register|sign up/i }));

    expect(screen.getByRole("button", { name: /registering/i })).toBeDisabled();
  });
});
