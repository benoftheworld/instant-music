import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { installMockWebSocket } from '@/tests/shared/mockWebSocket';

vi.mock('@/services/websocketService', () => {
  let connected = false;
  const listeners = new Map<string, Set<(data: any) => void>>();
  return {
    wsService: {
      connect: vi.fn(async () => { connected = true; }),
      disconnect: vi.fn(() => { connected = false; }),
      send: vi.fn(),
      on: vi.fn((event: string, cb: (data: any) => void) => {
        if (!listeners.has(event)) listeners.set(event, new Set());
        listeners.get(event)!.add(cb);
      }),
      off: vi.fn((event: string, cb: (data: any) => void) => {
        listeners.get(event)?.delete(cb);
      }),
      isConnected: vi.fn(() => connected),
    },
  };
});

class UseWebSocketTest {
  run() {
    describe('useWebSocket', () => {
      this.testReturnsInterface();
      this.testConnectsOnMount();
      this.testDisconnectsOnUnmount();
      this.testOnMessageReturnsUnsub();
      this.testNoConnectWithoutRoomCode();
    });
  }

  private testReturnsInterface() {
    it('retourne sendMessage, onMessage, isConnected', () => {
      const { result } = renderHook(() => useWebSocket('ABCD'));
      expect(result.current.sendMessage).toBeInstanceOf(Function);
      expect(result.current.onMessage).toBeInstanceOf(Function);
      expect(typeof result.current.isConnected).toBe('boolean');
    });
  }

  private testConnectsOnMount() {
    it('appelle wsService.connect au montage', async () => {
      const { wsService } = await import('@/services/websocketService');
      vi.clearAllMocks();
      renderHook(() => useWebSocket('ROOM1'));
      expect(wsService.connect).toHaveBeenCalledWith('ROOM1');
    });
  }

  private testDisconnectsOnUnmount() {
    it('appelle wsService.disconnect au démontage', async () => {
      const { wsService } = await import('@/services/websocketService');
      vi.clearAllMocks();
      const { unmount } = renderHook(() => useWebSocket('ROOM1'));
      unmount();
      expect(wsService.disconnect).toHaveBeenCalled();
    });
  }

  private testOnMessageReturnsUnsub() {
    it('onMessage retourne une fonction de désinscription', () => {
      const { result } = renderHook(() => useWebSocket('ROOM1'));
      const unsub = result.current.onMessage('test', vi.fn());
      expect(typeof unsub).toBe('function');
    });
  }

  private testNoConnectWithoutRoomCode() {
    it('ne connecte pas sans roomCode', async () => {
      const { wsService } = await import('@/services/websocketService');
      vi.clearAllMocks();
      renderHook(() => useWebSocket(undefined));
      expect(wsService.connect).not.toHaveBeenCalled();
    });
  }
}

new UseWebSocketTest().run();
