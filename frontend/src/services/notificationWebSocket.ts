/**
 * WebSocket service for user-specific notifications (invitations, etc.)
 * Connects to /ws/notifications/ and dispatches events to subscribers.
 */

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000';

type NotifCallback = (data: any) => void;

class NotificationWebSocketService {
  private socket: WebSocket | null = null;
  private listeners: Map<string, Set<NotifCallback>> = new Map();
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 3000;
  private intentionalDisconnect = false;

  connect(): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) return;

    this.intentionalDisconnect = false;
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) return;

    const url = `${WS_BASE_URL}/ws/notifications/?token=${accessToken}`;

    try {
      this.socket = new WebSocket(url);
    } catch {
      this._scheduleReconnect();
      return;
    }

    this.socket.onopen = () => {
      console.log('[NotificationWS] Connected');
      this.reconnectAttempts = 0;
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this._emit(data.type, data);
      } catch {
        // ignore malformed messages
      }
    };

    this.socket.onclose = () => {
      if (!this.intentionalDisconnect) {
        this._scheduleReconnect();
      }
    };

    this.socket.onerror = () => {
      // onerror always followed by onclose — handled there
    };
  }

  disconnect(): void {
    this.intentionalDisconnect = true;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  on(eventType: string, callback: NotifCallback): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(callback);
    return () => this.listeners.get(eventType)?.delete(callback);
  }

  private _emit(eventType: string, data: any): void {
    this.listeners.get(eventType)?.forEach((cb) => cb(data));
    // also emit '*' for catch-all subscribers
    this.listeners.get('*')?.forEach((cb) => cb(data));
  }

  private _scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * this.reconnectAttempts, 30_000);
    this.reconnectTimeout = setTimeout(() => {
      console.log(`[NotificationWS] Reconnecting (attempt ${this.reconnectAttempts})…`);
      this.connect();
    }, delay);
  }
}

// Singleton
export const notificationWS = new NotificationWebSocketService();
