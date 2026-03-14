import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { installMockWebSocket } from '@/tests/shared/mockWebSocket';

vi.mock('@/services/tokenService', () => ({
  tokenService: {
    getAccessToken: vi.fn(() => 'mock-token'),
    setAccessToken: vi.fn(),
    clearTokens: vi.fn(),
    isTokenExpired: vi.fn(() => false),
  },
}));

// Must re-import after mock
let notificationWS: typeof import('@/services/notificationWebSocket').notificationWS;

class NotificationWebSocketTest {
  private mockWS!: ReturnType<typeof installMockWebSocket>;

  run() {
    describe('NotificationWebSocketService', () => {
      beforeEach(async () => {
        vi.useFakeTimers();
        this.mockWS = installMockWebSocket();
        // Dynamic import to get fresh module instance
        const mod = await import('@/services/notificationWebSocket');
        notificationWS = mod.notificationWS;
      });

      afterEach(() => {
        notificationWS.disconnect();
        this.mockWS.restore();
        vi.useRealTimers();
      });

      this.testConnect();
      this.testDisconnect();
      this.testOnEvent();
      this.testWildcardListener();
      this.testUnsubscribe();
      this.testReconnectOnClose();
      this.testNoConnectWithoutToken();
    });
  }

  private testConnect() {
    it('connect — ouvre une connexion WebSocket', () => {
      notificationWS.connect();
      const instance = this.mockWS.getLastInstance();
      expect(instance).toBeDefined();
    });
  }

  private testDisconnect() {
    it('disconnect — ferme la connexion', () => {
      notificationWS.connect();
      notificationWS.disconnect();
      // Should not throw
    });
  }

  private testOnEvent() {
    it('on — reçoit les événements par type', () => {
      const handler = vi.fn();
      notificationWS.on('game_invitation', handler);
      notificationWS.connect();
      const instance = this.mockWS.getLastInstance()!;
      instance._simulateOpen();
      instance._simulateMessage({ type: 'game_invitation', data: {} });
      expect(handler).toHaveBeenCalledWith({ type: 'game_invitation', data: {} });
    });
  }

  private testWildcardListener() {
    it('on("*") — reçoit tous les événements', () => {
      const handler = vi.fn();
      notificationWS.on('*', handler);
      notificationWS.connect();
      const instance = this.mockWS.getLastInstance()!;
      instance._simulateOpen();
      instance._simulateMessage({ type: 'any_event' });
      expect(handler).toHaveBeenCalled();
    });
  }

  private testUnsubscribe() {
    it('on retourne un unsubscribe', () => {
      const handler = vi.fn();
      const unsub = notificationWS.on('test', handler);
      unsub();
      notificationWS.connect();
      const instance = this.mockWS.getLastInstance()!;
      instance._simulateOpen();
      instance._simulateMessage({ type: 'test' });
      expect(handler).not.toHaveBeenCalled();
    });
  }

  private testReconnectOnClose() {
    it('schedule reconnect on unintended close', () => {
      notificationWS.connect();
      const instance = this.mockWS.getLastInstance()!;
      instance._simulateOpen();
      instance._simulateClose(1006, 'Abnormal');
      vi.advanceTimersByTime(5000);
      // A new instance should have been created
      expect(this.mockWS.getAllInstances().length).toBeGreaterThan(1);
    });
  }

  private testNoConnectWithoutToken() {
    it('ne connecte pas sans access token', async () => {
      const { tokenService } = await import('@/services/tokenService');
      (tokenService.getAccessToken as ReturnType<typeof vi.fn>).mockReturnValueOnce(null);
      notificationWS.connect();
      expect(this.mockWS.getLastInstance()).toBeUndefined();
    });
  }
}

new NotificationWebSocketTest().run();
