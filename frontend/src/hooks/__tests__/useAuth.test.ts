import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useAuth } from "../useAuth";
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

describe("useAuth", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset the auth store
    useAuthStore.getState().clearAuth();
  });

  describe("login", () => {
    it("calls authService.login and updates store on success", async () => {
      const mockUser = {
        id: "123",
        email: "test@example.com",
        skillLevel: "beginner",
      };
      vi.mocked(authService.login).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.login("test@example.com", "password123");
      });

      expect(authService.login).toHaveBeenCalledWith(
        "test@example.com",
        "password123",
      );
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual({
        id: "123",
        email: "test@example.com",
        createdAt: expect.any(String),
      });
    });

    it("throws error on login failure", async () => {
      const error = new Error("Invalid credentials");
      vi.mocked(authService.login).mockRejectedValue(error);

      const { result } = renderHook(() => useAuth());

      await expect(
        act(async () => {
          await result.current.login("test@example.com", "wrongpassword");
        }),
      ).rejects.toThrow("Invalid credentials");

      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe("logout", () => {
    it("calls authService.logout and clears store", async () => {
      // First login to set user
      const mockUser = {
        id: "123",
        email: "test@example.com",
        skillLevel: "beginner",
      };
      vi.mocked(authService.login).mockResolvedValue(mockUser);
      vi.mocked(authService.logout).mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.login("test@example.com", "password123");
      });

      expect(result.current.isAuthenticated).toBe(true);

      await act(async () => {
        await result.current.logout();
      });

      expect(authService.logout).toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBe(null);
    });
  });

  describe("refresh", () => {
    it("calls authService.refresh and updates store on success", async () => {
      const mockUser = {
        id: "123",
        email: "test@example.com",
        skillLevel: "intermediate",
      };
      vi.mocked(authService.refresh).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth());

      await act(async () => {
        await result.current.refresh();
      });

      expect(authService.refresh).toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(true);
    });
  });

  describe("isLoading", () => {
    it("sets isLoading during login", async () => {
      let resolveLogin: (value: unknown) => void;
      vi.mocked(authService.login).mockImplementation(
        () =>
          new Promise((resolve) => {
            resolveLogin = resolve;
          }),
      );

      const { result } = renderHook(() => useAuth());

      expect(result.current.isLoading).toBe(false);

      // Start login but don't await
      let loginPromise: Promise<void>;
      act(() => {
        loginPromise = result.current.login("test@example.com", "password123");
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(true);
      });

      // Resolve login
      await act(async () => {
        resolveLogin!({
          id: "123",
          email: "test@example.com",
          skillLevel: "beginner",
        });
        await loginPromise;
      });

      expect(result.current.isLoading).toBe(false);
    });
  });
});
