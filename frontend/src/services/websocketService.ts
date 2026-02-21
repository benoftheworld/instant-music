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
  private intentionalDisconnect = false;
  private connectId = 0; // Track connect generation to ignore stale callbacks

  getRoomCode(): string | null {
    return this.roomCode;
  }

  connect(roomCode: string): Promise<void> {
    // Clean up any existing connection first
    this._cleanupSocket();

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    this.roomCode = roomCode;
    this.reconnectAttempts = 0;
    this.intentionalDisconnect = false;
    const currentConnectId = ++this.connectId;

    const url = `${WS_BASE_URL}/ws/game/${roomCode}/`;
    console.log('Connecting to WebSocket:', url);

    return new Promise((resolve, reject) => {
      try {
        this.socket = new WebSocket(url);
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        reject(error);
        return;
      }

      let settled = false;

      this.socket.onopen = () => {
        // Ignore if a newer connect() call has taken over
        if (currentConnectId !== this.connectId) return;

        console.log('WebSocket connected to room:', roomCode);
        this.reconnectAttempts = 0;
        settled = true;
        resolve();
      };

      this.socket.onerror = () => {
        // onerror is always followed by onclose — let onclose handle rejection.
        // Only log if this wasn't an intentional disconnect.
        if (!this.intentionalDisconnect && currentConnectId === this.connectId) {
          console.warn('WebSocket connection error (will retry via onclose)');
        }
      };

      this.socket.onclose = (event) => {
        // Ignore if a newer connect() call has taken over
        if (currentConnectId !== this.connectId) return;

        console.log(`WebSocket closed (code: ${event.code}, reason: ${event.reason || 'none'})`);
        this._emitEvent('disconnect', { code: event.code, reason: event.reason });

        if (!settled) {
          settled = true;
          // Connection never opened — reject the promise only if not intentionally disconnected
          if (this.intentionalDisconnect) {
            // Resolve silently — disconnect() was called, not a real error
            resolve();
          } else {
            // Actual connection failure — attempt reconnect instead of hard-failing
            this._attemptReconnect();
            resolve(); // Don't reject — reconnect will handle it
          }
          return;
        }

        // Connection was open and then dropped — auto-reconnect if appropriate
        if (!this.intentionalDisconnect && this.roomCode) {
          this._attemptReconnect();
        }
      };

      this.socket.onmessage = (event) => {
        if (currentConnectId !== this.connectId) return;

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

  private _cleanupSocket() {
    if (this.socket) {
      // Detach handlers to prevent ghost events from old sockets
      this.socket.onopen = null;
      this.socket.onerror = null;
      this.socket.onclose = null;
      this.socket.onmessage = null;

      if (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING) {
        this.socket.close(1000, 'Cleanup');
      }
      this.socket = null;
    }
  }

  private _attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnect attempts reached');
      this._emitEvent('reconnect_failed', {});
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
    this.intentionalDisconnect = true;
    this.connectId++; // Invalidate any pending connect callbacks

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    this.roomCode = null;
    this._cleanupSocket();
    this.listeners.clear();
  }

  send(message: WebSocketMessage): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected (state:', this.socket?.readyState ?? 'null', ')');
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
