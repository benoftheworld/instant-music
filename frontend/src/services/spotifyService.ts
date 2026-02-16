/**
 * Spotify API service for playlist and track management
 */
import { api } from './api';
import { SpotifyPlaylist, SpotifyTrack } from '../types';

class SpotifyService {
  /**
   * Search for playlists on Spotify
   */
  async searchPlaylists(query: string, limit: number = 20): Promise<SpotifyPlaylist[]> {
    try {
      const response = await api.get('/playlists/playlists/search/', {
        params: { query, limit }
      });
      // Backend returns {playlists: [...], using_oauth: bool, mode: string}
      return response.data.playlists || response.data;
    } catch (error) {
      console.error('Failed to search playlists:', error);
      throw error;
    }
  }

  /**
   * Get a playlist by Spotify ID
   */
  async getPlaylist(spotifyId: string): Promise<SpotifyPlaylist> {
    try {
      const response = await api.get(`/playlists/playlists/spotify/${spotifyId}/`);
      return response.data;
    } catch (error) {
      console.error('Failed to get playlist:', error);
      throw error;
    }
  }

  /**
   * Get tracks from a playlist
   */
  async getPlaylistTracks(spotifyId: string, limit: number = 50): Promise<SpotifyTrack[]> {
    try {
      const response = await api.get(`/playlists/playlists/spotify/${spotifyId}/tracks/`, {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get playlist tracks:', error);
      throw error;
    }
  }

  /**
   * Get a track by Spotify ID
   */
  async getTrack(spotifyId: string): Promise<SpotifyTrack> {
    try {
      const response = await api.get(`/playlists/tracks/spotify/${spotifyId}/`);
      return response.data;
    } catch (error) {
      console.error('Failed to get track:', error);
      throw error;
    }
  }

  /**
   * Format track duration from milliseconds to MM:SS
   */
  formatDuration(durationMs: number): string {
    const totalSeconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }
}

export const spotifyService = new SpotifyService();
