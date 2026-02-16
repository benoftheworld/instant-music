import { api } from './api';

export interface SpotifyTokenInfo {
  id: number;
  username: string;
  token_type: string;
  expires_at: string;
  scope: string;
  is_expired: boolean;
  created_at: string;
  updated_at: string;
}

export interface SpotifyAuthResponse {
  authorization_url: string;
  state: string;
}

class SpotifyAuthService {
  /**
   * Get Spotify OAuth authorization URL
   */
  async getAuthorizationUrl(): Promise<SpotifyAuthResponse> {
    const response = await api.get<SpotifyAuthResponse>('/playlists/spotify/authorize/');
    return response.data;
  }

  /**
   * Initiate Spotify OAuth flow
   * Opens popup window for Spotify login
   */
  async connectSpotify(): Promise<void> {
    const { authorization_url } = await this.getAuthorizationUrl();
    
    // Open Spotify OAuth in popup
    const width = 600;
    const height = 700;
    const left = window.screen.width / 2 - width / 2;
    const top = window.screen.height / 2 - height / 2;
    
    const popup = window.open(
      authorization_url,
      'Spotify Authorization',
      `width=${width},height=${height},left=${left},top=${top},toolbar=0,scrollbars=1,status=1,resizable=1,location=1,menuBar=0`
    );

    if (!popup) {
      throw new Error('Popup blocked. Please allow popups for this site.');
    }

    // Poll for popup close or URL change
    return new Promise((resolve, reject) => {
      const pollTimer = window.setInterval(() => {
        if (popup.closed) {
          window.clearInterval(pollTimer);
          resolve();
        }
      }, 500);

      // Timeout after 5 minutes
      setTimeout(() => {
        window.clearInterval(pollTimer);
        if (!popup.closed) {
          popup.close();
        }
        reject(new Error('Authentication timeout'));
      }, 5 * 60 * 1000);
    });
  }

  /**
   * Get current Spotify connection status
   */
  async getStatus(): Promise<SpotifyTokenInfo | null> {
    try {
      const response = await api.get<SpotifyTokenInfo>('/playlists/spotify/status/');
      return response.data;
    } catch (error: unknown) {
      const err = error as { response?: { status?: number } };
      if (err.response?.status === 404) {
        return null; // Not connected
      }
      throw error;
    }
  }

  /**
   * Disconnect Spotify account
   */
  async disconnect(): Promise<void> {
    await api.post('/playlists/spotify/disconnect/');
  }

  /**
   * Manually refresh Spotify token
   */
  async refresh(): Promise<SpotifyTokenInfo> {
    const response = await api.post<SpotifyTokenInfo>('/playlists/spotify/refresh/');
    return response.data;
  }

  /**
   * Check if user has active Spotify connection
   */
  async isConnected(): Promise<boolean> {
    const status = await this.getStatus();
    return status !== null && !status.is_expired;
  }
}

export const spotifyAuthService = new SpotifyAuthService();
export default spotifyAuthService;
