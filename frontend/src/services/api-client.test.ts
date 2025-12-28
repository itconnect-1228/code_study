import { describe, it, expect } from "vitest";
import { apiClient } from "./api-client";

describe("apiClient", () => {
  it("should be defined", () => {
    expect(apiClient).toBeDefined();
  });

  it("should have base URL with /api/v1", () => {
    expect(apiClient.defaults.baseURL).toContain("/api/v1");
  });

  it("should have withCredentials set to true", () => {
    expect(apiClient.defaults.withCredentials).toBe(true);
  });

  it("should have Content-Type header set to application/json", () => {
    expect(apiClient.defaults.headers["Content-Type"]).toBe("application/json");
  });

  it("should have Accept header set to application/json", () => {
    expect(apiClient.defaults.headers["Accept"]).toBe("application/json");
  });

  it("should have a reasonable timeout configured", () => {
    expect(apiClient.defaults.timeout).toBeGreaterThan(0);
    expect(apiClient.defaults.timeout).toBeLessThanOrEqual(60000);
  });

  it("should have request interceptors registered", () => {
    expect(apiClient.interceptors.request).toBeDefined();
    // Axios registers interceptors internally with handlers array
    expect(
      (apiClient.interceptors.request as unknown as { handlers: unknown[] })
        .handlers.length,
    ).toBeGreaterThan(0);
  });

  it("should have response interceptors registered", () => {
    expect(apiClient.interceptors.response).toBeDefined();
    expect(
      (apiClient.interceptors.response as unknown as { handlers: unknown[] })
        .handlers.length,
    ).toBeGreaterThan(0);
  });
});
