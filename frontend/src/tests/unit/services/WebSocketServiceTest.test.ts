import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { installMockWebSocket } from '@/tests/shared/mockWebSocket';

// We need to mock tokenService before importing WebSocketService
vi.mock('@/services/tokenService', () => ({
  tokenService: {
    getAccessToken: vi.fn(() => 'mock-token'),
    setAccessToken: vi.fn(),
    clearTokens: vi.fn(),
    isTokenExpired: vi.fn(() => false),
  },
}));

import { WebSocketService } from '@/services/websocketService';

class WebSocketServiceTest {
  private ws!: WebSocketService;
  private mockWS!: ReturnType<typeof installMockWebSocket>;

  run() {
    describe('WebSocketService', () => {
      beforeEach(() => {
        vi.useFakeTimers();
        this.mockWS = installMockWebSocket();
        this.ws = new WebSocketService();
      });

      afterEach(() => {
        this.ws.disconnect();
        this.mockWS.restore();
        vi.useRealTimers();
      });

      this.testConnect();
      this.testDisconnect();
      this.testSendMessage();
      this.testOnMessageListener();
      this.testOnTypedListener();
      this.testOffListener();
      this.testIsConnected();
      this.testGetRoomCode();
      this.testReconnectOnDrop();
    });
  }

  private testConnect() {
    it('connect — ouvre une connexion WebSocket', async () => {
      const promise = this.ws.connect('ABC123');
      const instance = this.mockWS.getLastInstance()!;
      instance._simulateOpen();
      await promise;
      expect(this.ws.isConnected()).toBe(true);
      expect(this.ws.getRoomCode()).toBe('ABC123');
    });
  }

  private testDisconnect() {
    it('disconnect — ferme la connexion', async () => {
      const promise = this.ws.connect('ABC123');
      this.mockWS.getLastInstance()!._simulateOpen();
      await promise;
      this.ws.disconnect();
      expect(this.ws.isConnected()).toBe(false);
      expect(this.ws.getRoomCode()).toBeNull();
    });
  }

  private testSendMessage() {
    it('send — envoie un message JSON', async () => {
      const promise = this.ws.connect('ABC123');
      const instance = this.mockWS.getLastInstance()!;
      instance._simulateOpen();
      await promise;
      this.ws.send({ type: 'player_answer', answer: 'test' });
      expect(instance.send).toHaveBeenCalledWith(JSON.stringify({ type: 'player_answer', answer: 'test' }));
    });
  }

  private testOnMessageListener() {
    it('on("message") — reçoit les messages', async () => {
      const handler = vi.fn();
      this.ws.on('message', handler);
      const promise = this.ws.connect('ABC123');
      const instance = this.mockWS.getLastInstance()!;
      instance._simulateOpen();
      await promise;
      instance._simulateMessage({ type: 'start_round', round: 1 });
      expect(handler).toHaveBeenCalledWith({ type: 'start_round', round: 1 });
    });
  }

  private testOnTypedListener() {
    it('on(type) — écoute un type spécifique', async () => {
      const handler = vi.fn();
      this.ws.on('start_round', handler);
      const promise = this.ws.connect('ABC123');
      const instance = this.mockWS.getLastInstance()!;
      instance._simulateOpen();
      await promise;
      instance._simulateMessage({ type: 'start_round', round: 1 });
      expect(handler).toHaveBeenCalled();
    });
  }

  private testOffListener() {
    it('off — supprime un listener', async () => {
      const handler = vi.fn();
      this.ws.on('message', handler);
      this.ws.off('message', handler);
      const promise = this.ws.connect('ABC123');
      const instance = this.mockWS.getLastInstance()!;
      instance._simulateOpen();
      await promise;
      instance._simulateMessage({ type: 'test' });
      expect(handler).not.toHaveBeenCalled();
    });
  }

  private testIsConnected() {
    it('isConnected — false avant connexion', () => {
      expect(this.ws.isConnected()).toBe(false);
    });
  }

  private testGetRoomCode() {
    it('getRoomCode — null par défaut', () => {
      expect(this.ws.getRoomCode()).toBeNull();
    });
  }

  private testReconnectOnDrop() {
    it('tente une reconnexion automatique après une coupure', async () => {
      const disconnectHandler = vi.fn();
      this.ws.on('disconnect', disconnectHandler);

      const promise = this.ws.connect('ABC123');
      const instance = this.mockWS.getLastInstance()!;
      instance._simulateOpen();
      await promise;

      // Simulate connection drop
      instance._simulateClose(1006, 'Abnormal');
      expect(disconnectHandler).toHaveBeenCalled();

      // Advance timer to trigger reconnect
      vi.advanceTimersByTime(3000);
      // A new WebSocket instance should have been created
      expect(this.mockWS.getAllInstances().length).toBeGreaterThan(1);
    });
  }
}

new WebSocketServiceTest().run();
