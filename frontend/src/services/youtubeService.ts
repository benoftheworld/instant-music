/**
 * YouTube API service for playlist and video management
 * Replaces Spotify service
 */
import { api } from './api';
import type { YouTubePlaylist, YouTubeTrack } from '@/types';

class YouTubeService {
  /**
   * Search for playlists on YouTube
   */
  async searchPlaylists(query: string, limit: number = 20): Promise<YouTubePlaylist[]> {
    try {
      const response = await api.get('/playlists/search/', {
        params: { query, limit }
      });
      const raw = response.data.playlists || response.data;
      // Map backend playlist_id → youtube_id (kept for interface compat)
      return raw.map((p: any) => ({
        youtube_id: p.playlist_id || p.youtube_id,
        name: p.name,
        description: p.description || '',
        image_url: p.image_url || '',
        total_tracks: p.total_tracks || 0,
        owner: p.owner || '',
        external_url: p.external_url || '',
      }));
    } catch (error) {
      console.error('Failed to search playlists:', error);
      throw error;
    }
  }

  /**
   * Get a playlist by YouTube ID
   */
  async getPlaylist(youtubeId: string): Promise<YouTubePlaylist> {
    try {
      const response = await api.get(`/playlists/${youtubeId}/`);
      const p = response.data;
      return {
        youtube_id: p.playlist_id || p.youtube_id,
        name: p.name,
        description: p.description || '',
        image_url: p.image_url || '',
        total_tracks: p.total_tracks || 0,
        owner: p.owner || '',
        external_url: p.external_url || '',
      };
    } catch (error) {
      console.error('Failed to get playlist:', error);
      throw error;
    }
  }

  /**
   * Get tracks from a YouTube playlist
   */
  async getPlaylistTracks(youtubeId: string, limit: number = 50): Promise<YouTubeTrack[]> {
    try {
      const response = await api.get(`/playlists/${youtubeId}/tracks/`, {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get playlist tracks:', error);
      throw error;
    }
  }

  /**
   * Search for individual YouTube songs (for karaoke mode).
   * Returns tracks with youtube_id, name, artists, duration_ms, album_image.
   */
  async searchYouTubeSongs(query: string, limit: number = 10): Promise<YouTubeTrack[]> {
    try {
      const response = await api.get('/playlists/youtube-songs/search/', {
        params: { query, limit },
      });
      return response.data.tracks || [];
    } catch (error) {
      console.error('Failed to search YouTube songs:', error);
      throw error;
    }
  }

  /**
   * Extract YouTube video ID from a URL
   */
  getVideoId(url: string): string | null {
    const match = url.match(/(?:v=|\/)([\w-]{11})(?:\?|&|$)/);
    return match ? match[1] : null;
  }

  /**
   * Get YouTube embed URL for a video
   */
  getEmbedUrl(videoId: string, autoplay: boolean = true): string {
    const params = new URLSearchParams({
      autoplay: autoplay ? '1' : '0',
      controls: '0',
      modestbranding: '1',
      rel: '0',
      showinfo: '0',
      enablejsapi: '1',
      origin: window.location.origin,
    });
    return `https://www.youtube.com/embed/${videoId}?${params.toString()}`;
  }
}

export const youtubeService = new YouTubeService();
