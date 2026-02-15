import { io, Socket } from 'socket.io-client';
import type { WebSocketMessage } from '@/types';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export class WebSocketService {
  private socket: Socket | null = null;
  private roomCode: string | null = null;

  connect(roomCode: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.roomCode = roomCode;
      this.socket = io(`${WS_URL}/ws/game/${roomCode}/`, {
        transports: ['websocket'],
      });

      this.socket.on('connect', () => {
        console.log('WebSocket connected');
        resolve();
      });

      this.socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        reject(error);
      });

      this.socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
      });
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.roomCode = null;
    }
  }

  send(message: WebSocketMessage): void {
    if (this.socket && this.socket.connected) {
      this.socket.emit('message', message);
    } else {
      console.error('WebSocket is not connected');
    }
  }

  on(event: string, callback: (data: any) => void): void {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  off(event: string, callback?: (data: any) => void): void {
    if (this.socket) {
      this.socket.off(event, callback);
    }
  }

  isConnected(): boolean {
    return this.socket !== null && this.socket.connected;
  }
}

export const wsService = new WebSocketService();
