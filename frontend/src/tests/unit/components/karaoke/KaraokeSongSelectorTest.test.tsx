import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

const mockListKaraokeSongs = vi.fn();

vi.mock('@/services/gameService', () => ({
  gameService: {
    listKaraokeSongs: (...args: unknown[]) => mockListKaraokeSongs(...args),
  },
}));

import KaraokeSongSelector from '@/components/karaoke/KaraokeSongSelector';
import type { KaraokeSong } from '@/types';

function makeSong(overrides: Partial<KaraokeSong> = {}): KaraokeSong {
  return {
    id: 1,
    title: 'Papaoutai',
    artist: 'Stromae',
    youtube_video_id: 'yt123',
    lrclib_id: 42,
    album_image_url: 'https://img.test/album.jpg',
    duration_ms: 230000,
    duration_display: '3:50',
    is_active: true,
    ...overrides,
  };
}

class KaraokeSongSelectorTest {
  run() {
    describe('KaraokeSongSelector', () => {
      beforeEach(() => {
        vi.clearAllMocks();
      });

      this.testLoadingState();
      this.testErrorState();
      this.testRendersSongs();
      this.testSearchFilter();
      this.testSelectSong();
      this.testSelectedSongView();
      this.testDeselectSong();
      this.testEmptyCatalogue();
      this.testSyncBadge();
    });
  }

  private testLoadingState() {
    it('affiche le chargement', () => {
      mockListKaraokeSongs.mockReturnValue(new Promise(() => {}));
      render(<KaraokeSongSelector selectedSong={null} onSelectSong={() => {}} />);
      expect(screen.getByText(/Chargement du catalogue/)).toBeInTheDocument();
    });
  }

  private testErrorState() {
    it('affiche un message d\'erreur', async () => {
      mockListKaraokeSongs.mockRejectedValue(new Error('fail'));
      render(<KaraokeSongSelector selectedSong={null} onSelectSong={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText(/Impossible de charger/)).toBeInTheDocument();
      });
    });
  }

  private testRendersSongs() {
    it('affiche la liste des morceaux', async () => {
      mockListKaraokeSongs.mockResolvedValue([makeSong(), makeSong({ id: 2, title: 'Alors on danse', artist: 'Stromae' })]);
      render(<KaraokeSongSelector selectedSong={null} onSelectSong={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText('Papaoutai')).toBeInTheDocument();
        expect(screen.getByText('Alors on danse')).toBeInTheDocument();
      });
    });
  }

  private testSearchFilter() {
    it('filtre par recherche', async () => {
      mockListKaraokeSongs.mockResolvedValue([makeSong(), makeSong({ id: 2, title: 'Formidable' })]);
      render(<KaraokeSongSelector selectedSong={null} onSelectSong={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText('Papaoutai')).toBeInTheDocument();
      });
      fireEvent.change(screen.getByPlaceholderText(/Rechercher par titre ou artiste/), { target: { value: 'Formidable' } });
      expect(screen.getByText('Formidable')).toBeInTheDocument();
      expect(screen.queryByText('Papaoutai')).not.toBeInTheDocument();
    });
  }

  private testSelectSong() {
    it('appelle onSelectSong au clic', async () => {
      const song = makeSong();
      mockListKaraokeSongs.mockResolvedValue([song]);
      const onSelect = vi.fn();
      render(<KaraokeSongSelector selectedSong={null} onSelectSong={onSelect} />);
      await waitFor(() => {
        expect(screen.getByText('Papaoutai')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Papaoutai'));
      expect(onSelect).toHaveBeenCalledWith(song);
    });
  }

  private testSelectedSongView() {
    it('affiche le morceau sélectionné', () => {
      const song = makeSong();
      render(<KaraokeSongSelector selectedSong={song} onSelectSong={() => {}} />);
      expect(screen.getByText('Morceau sélectionné', { exact: false })).toBeInTheDocument();
      expect(screen.getByText('Papaoutai')).toBeInTheDocument();
      expect(screen.getByText('Stromae')).toBeInTheDocument();
      expect(screen.getByText(/3:50/)).toBeInTheDocument();
    });
  }

  private testDeselectSong() {
    it('permet de changer de morceau', () => {
      const onSelect = vi.fn();
      render(<KaraokeSongSelector selectedSong={makeSong()} onSelectSong={onSelect} />);
      fireEvent.click(screen.getByTitle('Changer de morceau'));
      expect(onSelect).toHaveBeenCalledWith(null);
    });
  }

  private testEmptyCatalogue() {
    it('affiche un catalogue vide', async () => {
      mockListKaraokeSongs.mockResolvedValue([]);
      render(<KaraokeSongSelector selectedSong={null} onSelectSong={() => {}} />);
      await waitFor(() => {
        expect(screen.getByText('Catalogue vide')).toBeInTheDocument();
      });
    });
  }

  private testSyncBadge() {
    it('affiche le badge paroles synchronisées', () => {
      const song = makeSong({ lrclib_id: 42 });
      render(<KaraokeSongSelector selectedSong={song} onSelectSong={() => {}} />);
      expect(screen.getByText(/Paroles synchronisées/)).toBeInTheDocument();
    });
  }
}

new KaraokeSongSelectorTest().run();
