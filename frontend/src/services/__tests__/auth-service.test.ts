import { describe, it, expect, vi, beforeEach } from "vitest";
import { authService } from "../auth-service";
import { apiClient } from "../api-client";

vi.mock("../api-client");

describe("authService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("register", () => {
    it("calls POST /auth/register with email and password (auto-login)", async () => {
      // Backend now returns LoginResponse (tokens + user) for auto-login
      const mockResponse = {
        data: {
          access_token: "mock-token",
          token_type: "bearer",
          user: {
            id: "1",
            email: "test@example.com",
            skill_level: "beginner",
          },
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await authService.register(
        "test@example.com",
        "password123",
      );

      expect(apiClient.post).toHaveBeenCalledWith("/auth/register", {
        email: "test@example.com",
        password: "password123",
      });

      expect(result).toEqual({
        id: "1",
        email: "test@example.com",
        skillLevel: "beginner",
      });
    });
  });

  describe("login", () => {
    it("calls POST /auth/login with email and password", async () => {
      const mockResponse = {
        data: {
          access_token: "mock-token",
          token_type: "bearer",
          user: {
            id: "1",
            email: "test@example.com",
            skill_level: "beginner",
          },
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await authService.login("test@example.com", "password123");

      expect(apiClient.post).toHaveBeenCalledWith("/auth/login", {
        email: "test@example.com",
        password: "password123",
      });

      expect(result).toEqual({
        id: "1",
        email: "test@example.com",
        skillLevel: "beginner",
      });
    });
  });

  describe("logout", () => {
    it("calls POST /auth/logout", async () => {
      vi.mocked(apiClient.post).mockResolvedValue({ data: {} });

      await authService.logout();

      expect(apiClient.post).toHaveBeenCalledWith("/auth/logout");
    });
  });

  describe("refresh", () => {
    it("calls POST /auth/refresh", async () => {
      const mockResponse = {
        data: {
          access_token: "new-token",
          token_type: "bearer",
          user: {
            id: "1",
            email: "test@example.com",
            skill_level: "beginner",
          },
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await authService.refresh();

      expect(apiClient.post).toHaveBeenCalledWith("/auth/refresh");

      expect(result).toEqual({
        id: "1",
        email: "test@example.com",
        skillLevel: "beginner",
      });
    });
  });
});
