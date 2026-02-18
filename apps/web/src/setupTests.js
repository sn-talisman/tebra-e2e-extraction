import '@testing-library/jest-dom';

// ResizeObserver polyfill for Recharts
global.ResizeObserver = class ResizeObserver {
    observe() { }
    unobserve() { }
    disconnect() { }
};
