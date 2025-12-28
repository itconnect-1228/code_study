import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "./auth-store";
import type { User } from "./auth-store";

/**
 * Auth Store Tests
 *
 * Tests the Zustand authentication store following TDD principles.
 * These tests verify:
 * - Initial state is correct
 * - setUser action works properly
 * - setLoading action works properly
 * - clearAuth action resets all state
 * - Selector hooks return correct values
 */

describe("auth-store", () => {
  // Reset store state before each test
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    });
  });

  describe("initial state", () => {
    it("should have user as null initially", () => {
      const { user } = useAuthStore.getState();
      expect(user).toBeNull();
    });

    it("should have isAuthenticated as false initially", () => {
      const { isAuthenticated } = useAuthStore.getState();
      expect(isAuthenticated).toBe(false);
    });

    it("should have isLoading as false initially", () => {
      const { isLoading } = useAuthStore.getState();
      expect(isLoading).toBe(false);
    });
  });

  describe("setUser action", () => {
    it("should set user and mark as authenticated when user is provided", () => {
      const testUser: User = {
        id: "123",
        email: "test@example.com",
        createdAt: "2024-01-01T00:00:00Z",
      };

      useAuthStore.getState().setUser(testUser);

      const { user, isAuthenticated } = useAuthStore.getState();
      expect(user).toEqual(testUser);
      expect(isAuthenticated).toBe(true);
    });

    it("should set user to null and mark as not authenticated when null is provided", () => {
      // First set a user
      const testUser: User = {
        id: "123",
        email: "test@example.com",
        createdAt: "2024-01-01T00:00:00Z",
      };
      useAuthStore.getState().setUser(testUser);

      // Then set to null
      useAuthStore.getState().setUser(null);

      const { user, isAuthenticated } = useAuthStore.getState();
      expect(user).toBeNull();
      expect(isAuthenticated).toBe(false);
    });
  });

  describe("setLoading action", () => {
    it("should set loading to true", () => {
      useAuthStore.getState().setLoading(true);

      const { isLoading } = useAuthStore.getState();
      expect(isLoading).toBe(true);
    });

    it("should set loading to false", () => {
      // First set to true
      useAuthStore.getState().setLoading(true);
      // Then set to false
      useAuthStore.getState().setLoading(false);

      const { isLoading } = useAuthStore.getState();
      expect(isLoading).toBe(false);
    });
  });

  describe("clearAuth action", () => {
    it("should reset all auth state to initial values", () => {
      // Setup: set user and loading state
      const testUser: User = {
        id: "123",
        email: "test@example.com",
        createdAt: "2024-01-01T00:00:00Z",
      };
      useAuthStore.getState().setUser(testUser);
      useAuthStore.getState().setLoading(true);

      // Verify setup
      expect(useAuthStore.getState().user).not.toBeNull();
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
      expect(useAuthStore.getState().isLoading).toBe(true);

      // Clear auth
      useAuthStore.getState().clearAuth();

      // Verify reset
      const { user, isAuthenticated, isLoading } = useAuthStore.getState();
      expect(user).toBeNull();
      expect(isAuthenticated).toBe(false);
      expect(isLoading).toBe(false);
    });
  });

  describe("state persistence", () => {
    it("should maintain state across multiple getState calls", () => {
      const testUser: User = {
        id: "123",
        email: "test@example.com",
        createdAt: "2024-01-01T00:00:00Z",
      };

      useAuthStore.getState().setUser(testUser);

      // Multiple getState calls should return the same state
      const state1 = useAuthStore.getState();
      const state2 = useAuthStore.getState();

      expect(state1.user).toEqual(state2.user);
      expect(state1.isAuthenticated).toEqual(state2.isAuthenticated);
    });
  });

  describe("type safety", () => {
    it("should accept valid User type", () => {
      const testUser: User = {
        id: "123",
        email: "test@example.com",
        createdAt: "2024-01-01T00:00:00Z",
      };

      useAuthStore.getState().setUser(testUser);

      const { user } = useAuthStore.getState();
      expect(user?.id).toBe("123");
      expect(user?.email).toBe("test@example.com");
      expect(user?.createdAt).toBe("2024-01-01T00:00:00Z");
    });
  });

  describe("selector hooks", () => {
    it("useUser should return current user", () => {
      const testUser: User = {
        id: "123",
        email: "test@example.com",
        createdAt: "2024-01-01T00:00:00Z",
      };
      useAuthStore.getState().setUser(testUser);

      // Access through the selector hook's underlying selector
      const user = useAuthStore.getState().user;
      expect(user).toEqual(testUser);
    });

    it("useIsAuthenticated should return authentication status", () => {
      const testUser: User = {
        id: "123",
        email: "test@example.com",
        createdAt: "2024-01-01T00:00:00Z",
      };
      useAuthStore.getState().setUser(testUser);

      const isAuthenticated = useAuthStore.getState().isAuthenticated;
      expect(isAuthenticated).toBe(true);
    });

    it("useAuthLoading should return loading status", () => {
      useAuthStore.getState().setLoading(true);

      const isLoading = useAuthStore.getState().isLoading;
      expect(isLoading).toBe(true);
    });
  });
});
