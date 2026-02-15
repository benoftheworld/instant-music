import { useEffect, useCallback } from 'react';
import { wsService } from '@/services/websocketService';
import type { WebSocketMessage } from '@/types';

export const useWebSocket = (roomCode: string | undefined) => {
  useEffect(() => {
    if (!roomCode) return;

    const connect = async () => {
      try {
        await wsService.connect(roomCode);
      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
      }
    };

    connect();

    return () => {
      wsService.disconnect();
    };
  }, [roomCode]);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    wsService.send(message);
  }, []);

  const onMessage = useCallback((event: string, callback: (data: any) => void) => {
    wsService.on(event, callback);
    return () => wsService.off(event, callback);
  }, []);

  return {
    sendMessage,
    onMessage,
    isConnected: wsService.isConnected(),
  };
};
