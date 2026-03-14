/**
 * Mock WebSocket pour les tests unitaires.
 * Simule le comportement d'un WebSocket natif sans connexion réseau.
 */
import { vi } from 'vitest';

export interface MockWebSocketInstance {
  url: string;
  readyState: number;
  onopen: ((event: Event) => void) | null;
  onclose: ((event: CloseEvent) => void) | null;
  onmessage: ((event: MessageEvent) => void) | null;
  onerror: ((event: Event) => void) | null;
  send: ReturnType<typeof vi.fn>;
  close: ReturnType<typeof vi.fn>;

  // Méthodes utilitaires pour simuler le serveur
  _simulateOpen(): void;
  _simulateMessage(data: Record<string, unknown>): void;
  _simulateClose(code?: number, reason?: string): void;
  _simulateError(): void;
}

/** Toutes les instances créées pendant le test */
let instances: MockWebSocketInstance[] = [];

function createMockWebSocketInstance(url: string): MockWebSocketInstance {
  const instance: MockWebSocketInstance = {
    url,
    readyState: WebSocket.CONNECTING,
    onopen: null,
    onclose: null,
    onmessage: null,
    onerror: null,
    send: vi.fn(),
    close: vi.fn().mockImplementation(function (this: MockWebSocketInstance) {
      this.readyState = WebSocket.CLOSED;
      if (this.onclose) {
        this.onclose(new CloseEvent('close', { code: 1000, reason: 'Normal' }));
      }
    }),

    _simulateOpen() {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    },

    _simulateMessage(data: Record<string, unknown>) {
      if (this.onmessage) {
        this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
      }
    },

    _simulateClose(code = 1000, reason = 'Normal') {
      this.readyState = WebSocket.CLOSED;
      if (this.onclose) {
        this.onclose(new CloseEvent('close', { code, reason }));
      }
    },

    _simulateError() {
      if (this.onerror) {
        this.onerror(new Event('error'));
      }
    },
  };

  instances.push(instance);
  return instance;
}

/**
 * Installe le mock WebSocket global.
 * Retourne des helpers pour contrôler les instances.
 */
export function installMockWebSocket() {
  instances = [];
  const original = globalThis.WebSocket;

  // Use a real class so `new WebSocket(url)` works correctly
  class MockWSClass {
    static CONNECTING = 0;
    static OPEN = 1;
    static CLOSING = 2;
    static CLOSED = 3;

    constructor(url: string) {
      const instance = createMockWebSocketInstance(url);
      return instance as any;
    }
  }

  (globalThis as any).WebSocket = MockWSClass;

  return {
    MockWS: MockWSClass,
    /** Retourne la dernière instance WebSocket créée */
    getLastInstance: (): MockWebSocketInstance | undefined => instances[instances.length - 1],
    /** Retourne toutes les instances */
    getAllInstances: (): MockWebSocketInstance[] => instances,
    /** Restaure le WebSocket natif */
    restore: () => {
      (globalThis as any).WebSocket = original;
      instances = [];
    },
  };
}
