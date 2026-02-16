/**
 * WebSocket service using native WebSocket (compatible with Django Channels).
 * 
 * Django Channels uses native WebSocket protocol, NOT Socket.IO.
 */
import type { WebSocketMessage } from '@/types';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000';

type MessageCallback = (data: WebSocketMessage) => void;

export class WebSocketService {
  private socket: WebSocket | null = null;
  private roomCode: string | null = null;
  private listeners: Map<string, Set<MessageCallback>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

  getRoomCode(): string | null {
    return this.roomCode;
  }

  connect(roomCode: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.roomCode = roomCode;
      this.reconnectAttempts = 0;

      const url = `${WS_BASE_URL}/ws/game/${roomCode}/`;
      console.log('Connecting to WebSocket:', url);

      try {
        this.socket = new WebSocket(url);
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        reject(error);
        return;
      }

      this.socket.onopen = () => {
        console.log('WebSocket connected to room:', roomCode);
        this.reconnectAttempts = 0;
        resolve();
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };

      this.socket.onclose = (event) => {
        console.log(`WebSocket closed (code: ${event.code}, reason: ${event.reason})`);
        this._emitEvent('disconnect', { code: event.code, reason: event.reason });
        
        // Auto-reconnect if not intentionally closed
        if (event.code !== 1000 && this.roomCode) {
          this._attemptReconnect();
        }
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WebSocketMessage;
          
          // Emit to 'message' listeners (general)
          this._emitEvent('message', data);
          
          // Also emit by specific type (e.g., 'player_joined', 'game_started')
          if (data.type) {
            this._emitEvent(data.type, data);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
    });
  }

  private _attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

    this.reconnectTimeout = setTimeout(() => {
      if (this.roomCode) {
        this.connect(this.roomCode).catch((error) => {
          console.error('Reconnect failed:', error);
        });
      }
    }, delay);
  }

  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    this.roomCode = null;

    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }

    this.listeners.clear();
  }

  send(message: WebSocketMessage): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected (state:', this.socket?.readyState, ')');
    }
  }

  on(event: string, callback: MessageCallback): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback?: MessageCallback): void {
    if (!callback) {
      this.listeners.delete(event);
      return;
    }
    this.listeners.get(event)?.delete(callback);
  }

  private _emitEvent(event: string, data: any): void {
    this.listeners.get(event)?.forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in WebSocket listener for '${event}':`, error);
      }
    });
  }

  isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
}

export const wsService = new WebSocketService();
