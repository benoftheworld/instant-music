import '@testing-library/jest-dom';
import { afterEach, vi } from 'vitest';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key: (index: number) => Object.keys(store)[index] ?? null,
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock matchMedia (requis par certains composants UI / responsive)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
class IntersectionObserverMock {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}
Object.defineProperty(window, 'IntersectionObserver', {
  writable: true,
  value: IntersectionObserverMock,
});

// Mock URL.createObjectURL / revokeObjectURL (pour avatars, PDFs)
Object.defineProperty(URL, 'createObjectURL', { value: vi.fn(() => 'blob:mock-url') });
Object.defineProperty(URL, 'revokeObjectURL', { value: vi.fn() });

// Mock AudioContext (pour SoundEffects)
class AudioContextMock {
  state = 'running';
  resume = vi.fn().mockResolvedValue(undefined);
  close = vi.fn().mockResolvedValue(undefined);
  get currentTime() {
    return 0;
  }
  get destination() {
    return {};
  }
  createOscillator() {
    return {
      type: 'sine',
      frequency: { setValueAtTime: vi.fn() },
      connect: vi.fn(),
      start: vi.fn(),
      stop: vi.fn(),
    };
  }
  createGain() {
    return {
      gain: { setValueAtTime: vi.fn(), exponentialRampToValueAtTime: vi.fn() },
      connect: vi.fn(),
    };
  }
}
Object.defineProperty(window, 'AudioContext', { writable: true, value: AudioContextMock });

// Mock import.meta.env
if (!(import.meta as any).env) {
  (import.meta as any).env = {};
}

// Reset localStorage entre chaque test
afterEach(() => {
  localStorage.clear();
});
