import { useEffect, useCallback, useRef, useState } from 'react';
import { wsService } from '@/services/websocketService';
import type { WebSocketMessage } from '@/types';

export const useWebSocket = (roomCode: string | undefined) => {
  const [connected, setConnected] = useState(false);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    if (!roomCode) return;

    const connect = async () => {
      try {
        await wsService.connect(roomCode);
        if (mountedRef.current) {
          setConnected(true);
        }
      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
      }
    };

    connect();

    return () => {
      mountedRef.current = false;
      setConnected(false);
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
    isConnected: connected,
  };
};
