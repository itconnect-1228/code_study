import "@testing-library/jest-dom";

// ResizeObserver 모킹 (Radix UI 컴포넌트에서 필요)
(
  globalThis as typeof globalThis & { ResizeObserver: typeof ResizeObserver }
).ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
