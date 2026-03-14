import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BaseServiceTest } from '../base/BaseServiceTest';

vi.mock('@/services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import { youtubeService } from '@/services/youtubeService';
import { api } from '@/services/api';
import { createYouTubePlaylist, createYouTubeTrack } from '@/tests/shared/factories';

class YouTubeServiceTest extends BaseServiceTest {
  protected name = 'youtubeService';

  run() {
    describe('youtubeService', () => {
      this.setup(api);

      this.testSearchPlaylists();
      this.testGetPlaylist();
      this.testGetPlaylistTracks();
      this.testSearchYouTubeSongs();
      this.testGetVideoId();
      this.testGetVideoIdInvalid();
      this.testGetEmbedUrl();
      this.testSearchPlaylistsError();
    });
  }

  private testSearchPlaylists() {
    it('searchPlaylists — succès', async () => {
      const playlists = [{ playlist_id: 'PL1', name: 'Test', description: '', image_url: '', total_tracks: 10, owner: 'Me', external_url: '' }];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { playlists } });
      const result = await youtubeService.searchPlaylists('test');
      expect(result).toHaveLength(1);
      expect(result[0].youtube_id).toBe('PL1');
    });
  }

  private testGetPlaylist() {
    it('getPlaylist — succès', async () => {
      const raw = { playlist_id: 'PL1', name: 'Test', description: '', image_url: '', total_tracks: 5, owner: 'Me', external_url: '' };
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: raw });
      const result = await youtubeService.getPlaylist('PL1');
      expect(result.youtube_id).toBe('PL1');
      expect(result.name).toBe('Test');
    });
  }

  private testGetPlaylistTracks() {
    it('getPlaylistTracks — succès', async () => {
      const tracks = [createYouTubeTrack()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: tracks });
      const result = await youtubeService.getPlaylistTracks('PL1');
      expect(result).toEqual(tracks);
    });
  }

  private testSearchYouTubeSongs() {
    it('searchYouTubeSongs — succès', async () => {
      const tracks = [createYouTubeTrack()];
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { tracks } });
      const result = await youtubeService.searchYouTubeSongs('bohemian');
      expect(result).toEqual(tracks);
    });
  }

  private testGetVideoId() {
    it('getVideoId — extrait l\'ID d\'une URL YouTube', () => {
      expect(youtubeService.getVideoId('https://www.youtube.com/watch?v=dQw4w9WgXcQ')).toBe('dQw4w9WgXcQ');
      expect(youtubeService.getVideoId('https://youtu.be/dQw4w9WgXcQ')).toBe('dQw4w9WgXcQ');
    });
  }

  private testGetVideoIdInvalid() {
    it('getVideoId — retourne null pour URL invalide', () => {
      expect(youtubeService.getVideoId('https://example.com')).toBeNull();
      expect(youtubeService.getVideoId('')).toBeNull();
    });
  }

  private testGetEmbedUrl() {
    it('getEmbedUrl — génère l\'URL embed correcte', () => {
      const url = youtubeService.getEmbedUrl('dQw4w9WgXcQ', true);
      expect(url).toContain('https://www.youtube.com/embed/dQw4w9WgXcQ');
      expect(url).toContain('autoplay=1');
    });
  }

  private testSearchPlaylistsError() {
    it('searchPlaylists — erreur réseau', async () => {
      (api.get as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Network'));
      await expect(youtubeService.searchPlaylists('test')).rejects.toThrow('Network');
    });
  }
}

new YouTubeServiceTest().run();
