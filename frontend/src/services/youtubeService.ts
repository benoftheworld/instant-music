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
      const response = await api.get('/playlists/playlists/search/', {
        params: { query, limit }
      });
      return response.data.playlists || response.data;
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
      const response = await api.get(`/playlists/playlists/youtube/${youtubeId}/`);
      return response.data;
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
      const response = await api.get(`/playlists/playlists/youtube/${youtubeId}/tracks/`, {
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
      const response = await api.get('/playlists/playlists/youtube-songs/search/', {
        params: { query, limit },
      });
      return response.data.tracks || [];
    } catch (error) {
      console.error('Failed to search YouTube songs:', error);
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
