import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';

const { mockSearchYouTubeSongs } = vi.hoisted(() => ({ mockSearchYouTubeSongs: vi.fn() }));

vi.mock('@/services/youtubeService', () => ({
  youtubeService: {
    searchYouTubeSongs: (...args: unknown[]) => mockSearchYouTubeSongs(...args),
  },
}));

vi.mock('@/components/ui', () => ({
  Spinner: ({ size }: any) => <span data-testid="spinner" data-size={size} />,
  EmptyState: ({ title, description }: any) => (
    <div data-testid="empty">
      <p>{title}</p>
      {description && <p>{description}</p>}
    </div>
  ),
}));

vi.mock('@/utils/format', () => ({
  formatDuration: (ms: number) => `${Math.floor(ms / 1000)}s`,
}));

import YouTubeSongSearch from '@/components/karaoke/YouTubeSongSearch';
import type { YouTubeTrack, KaraokeTrack } from '@/types';

function makeYTTrack(overrides: Partial<YouTubeTrack> = {}): YouTubeTrack {
  return {
    youtube_id: 'yt1',
    name: 'Bohemian Rhapsody',
    artists: ['Queen'],
    album: 'A Night at the Opera',
    album_image: 'https://img.test/cover.jpg',
    duration_ms: 354000,
    preview_url: null,
    external_url: 'https://yt.test/watch?v=yt1',
    ...overrides,
  };
}

function makeKaraokeTrack(): KaraokeTrack {
  return {
    youtube_video_id: 'yt1',
    track_name: 'Bohemian Rhapsody',
    artist_name: 'Queen',
    duration_ms: 354000,
    album_image: 'https://img.test/cover.jpg',
  };
}

class YouTubeSongSearchTest {
  run() {
    describe('YouTubeSongSearch', () => {
      beforeEach(() => {
        vi.clearAllMocks();
        vi.useFakeTimers();
      });

      afterEach(() => {
        vi.useRealTimers();
      });

      this.testInitialState();
      this.testSearchResults();
      this.testEmptyResults();
      this.testSelectTrack();
      this.testSelectedTrackView();
      this.testRemoveTrack();
      this.testSearchError();
      this.testShortQuery();
    });
  }

  private testInitialState() {
    it('affiche l\'état initial avec message de recherche', () => {
      render(<YouTubeSongSearch selectedTrack={null} onSelectTrack={() => {}} />);
      expect(screen.getByText(/Rechercher un morceau YouTube/)).toBeInTheDocument();
      expect(screen.getByText(/Recherchez un morceau pour lancer le karaoké/)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Bohemian Rhapsody/)).toBeInTheDocument();
    });
  }

  private testSearchResults() {
    it('affiche les résultats de recherche après saisie', async () => {
      mockSearchYouTubeSongs.mockResolvedValue([makeYTTrack()]);
      render(<YouTubeSongSearch selectedTrack={null} onSelectTrack={() => {}} />);

      fireEvent.change(screen.getByPlaceholderText(/Bohemian Rhapsody/), { target: { value: 'Queen' } });

      // Advance past debounce and flush microtasks
      await act(async () => {
        await vi.advanceTimersByTimeAsync(600);
      });

      expect(screen.getByText('Bohemian Rhapsody')).toBeInTheDocument();
      expect(screen.getByText('Queen')).toBeInTheDocument();
      expect(mockSearchYouTubeSongs).toHaveBeenCalledWith('Queen', 8);
    });
  }

  private testEmptyResults() {
    it('affiche un état vide si pas de résultat', async () => {
      mockSearchYouTubeSongs.mockResolvedValue([]);
      render(<YouTubeSongSearch selectedTrack={null} onSelectTrack={() => {}} />);

      fireEvent.change(screen.getByPlaceholderText(/Bohemian Rhapsody/), { target: { value: 'xyznotfound' } });

      await act(async () => {
        await vi.advanceTimersByTimeAsync(600);
      });

      expect(screen.getByTestId('empty')).toBeInTheDocument();
    });
  }

  private testSelectTrack() {
    it('appelle onSelectTrack avec le format KaraokeTrack', async () => {
      mockSearchYouTubeSongs.mockResolvedValue([makeYTTrack()]);
      const onSelect = vi.fn();
      render(<YouTubeSongSearch selectedTrack={null} onSelectTrack={onSelect} />);

      fireEvent.change(screen.getByPlaceholderText(/Bohemian Rhapsody/), { target: { value: 'Queen' } });

      await act(async () => {
        await vi.advanceTimersByTimeAsync(600);
      });

      expect(screen.getByText('Bohemian Rhapsody')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Bohemian Rhapsody'));
      expect(onSelect).toHaveBeenCalledWith({
        youtube_video_id: 'yt1',
        track_name: 'Bohemian Rhapsody',
        artist_name: 'Queen',
        duration_ms: 354000,
        album_image: 'https://img.test/cover.jpg',
      });
    });
  }

  private testSelectedTrackView() {
    it('affiche le morceau sélectionné', () => {
      render(<YouTubeSongSearch selectedTrack={makeKaraokeTrack()} onSelectTrack={() => {}} />);
      expect(screen.getByText('Morceau sélectionné', { exact: false })).toBeInTheDocument();
      expect(screen.getByText('Bohemian Rhapsody')).toBeInTheDocument();
      expect(screen.getByText('Queen')).toBeInTheDocument();
    });
  }

  private testRemoveTrack() {
    it('permet de retirer le morceau sélectionné', () => {
      const onSelect = vi.fn();
      render(<YouTubeSongSearch selectedTrack={makeKaraokeTrack()} onSelectTrack={onSelect} />);
      fireEvent.click(screen.getByTitle('Retirer'));
      expect(onSelect).toHaveBeenCalledWith(null);
    });
  }

  private testSearchError() {
    it('affiche une erreur de recherche', async () => {
      mockSearchYouTubeSongs.mockRejectedValue(new Error('Network error'));
      render(<YouTubeSongSearch selectedTrack={null} onSelectTrack={() => {}} />);

      fireEvent.change(screen.getByPlaceholderText(/Bohemian Rhapsody/), { target: { value: 'test query' } });

      await act(async () => {
        await vi.advanceTimersByTimeAsync(600);
      });

      expect(screen.getByText(/Erreur lors de la recherche YouTube/)).toBeInTheDocument();
    });
  }

  private testShortQuery() {
    it('ne lance pas de recherche si la saisie est trop courte', async () => {
      render(<YouTubeSongSearch selectedTrack={null} onSelectTrack={() => {}} />);

      fireEvent.change(screen.getByPlaceholderText(/Bohemian Rhapsody/), { target: { value: 'Q' } });

      await act(async () => {
        await vi.advanceTimersByTimeAsync(500);
      });

      expect(mockSearchYouTubeSongs).not.toHaveBeenCalled();
    });
  }
}

new YouTubeSongSearchTest().run();
