import '@testing-library/jest-dom'

// ResizeObserver 모킹 (Radix UI 컴포넌트에서 필요)
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
