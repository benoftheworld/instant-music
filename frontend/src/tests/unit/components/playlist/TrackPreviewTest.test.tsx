import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

vi.mock('@/utils/format', () => ({
  formatTime: (s: number) => `${Math.floor(s)}s`,
  formatDuration: (ms: number) => `${Math.floor(ms / 1000)}s`,
}));

import TrackPreview from '@/components/playlist/TrackPreview';
import type { YouTubeTrack } from '@/types';

function makeTrack(overrides: Partial<YouTubeTrack> = {}): YouTubeTrack {
  return {
    youtube_id: 'yt1',
    name: 'Bohemian Rhapsody',
    artists: ['Queen'],
    album: 'A Night at the Opera',
    album_image: 'https://img.test/cover.jpg',
    duration_ms: 354000,
    preview_url: 'https://audio.test/preview.mp3',
    external_url: 'https://yt.test/watch?v=yt1',
    ...overrides,
  };
}

class TrackPreviewTest {
  run() {
    describe('TrackPreview', () => {
      beforeEach(() => {
        vi.clearAllMocks();
        // Mock HTMLAudioElement play/pause
        HTMLAudioElement.prototype.play = vi.fn().mockResolvedValue(undefined);
        HTMLAudioElement.prototype.pause = vi.fn();
      });

      this.testRendersTrackInfo();
      this.testRendersAlbumArt();
      this.testFallbackWhenNoImage();
      this.testPlayButton();
      this.testNoPreviewMessage();
      this.testHiddenControlsMode();
      this.testDurationBadge();
    });
  }

  private testRendersTrackInfo() {
    it('affiche le nom du morceau et les artistes', () => {
      render(<TrackPreview track={makeTrack()} />);
      expect(screen.getByText('Bohemian Rhapsody')).toBeInTheDocument();
      expect(screen.getByText(/Queen/)).toBeInTheDocument();
      expect(screen.getByText(/A Night at the Opera/)).toBeInTheDocument();
    });
  }

  private testRendersAlbumArt() {
    it('affiche la pochette d\'album', () => {
      render(<TrackPreview track={makeTrack()} />);
      const img = screen.getByAltText('A Night at the Opera');
      expect(img).toHaveAttribute('src', 'https://img.test/cover.jpg');
    });
  }

  private testFallbackWhenNoImage() {
    it('affiche un placeholder si pas d\'image', () => {
      render(<TrackPreview track={makeTrack({ album_image: '' })} />);
      expect(screen.queryByAltText('A Night at the Opera')).not.toBeInTheDocument();
    });
  }

  private testPlayButton() {
    it('affiche le bouton de lecture quand preview_url est présent', () => {
      render(<TrackPreview track={makeTrack()} />);
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  }

  private testNoPreviewMessage() {
    it('affiche un message si aperçu non disponible', () => {
      render(<TrackPreview track={makeTrack({ preview_url: null })} />);
      expect(screen.getByText('Aperçu non disponible')).toBeInTheDocument();
    });
  }

  private testHiddenControlsMode() {
    it('masque les contrôles si showControls=false', () => {
      render(<TrackPreview track={makeTrack()} showControls={false} />);
      expect(screen.queryByRole('button')).not.toBeInTheDocument();
      expect(screen.queryByText('Aperçu non disponible')).not.toBeInTheDocument();
    });
  }

  private testDurationBadge() {
    it('affiche la durée formatée', () => {
      render(<TrackPreview track={makeTrack({ duration_ms: 210000 })} />);
      expect(screen.getByText('210s')).toBeInTheDocument();
    });
  }
}

new TrackPreviewTest().run();
