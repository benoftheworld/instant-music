import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

vi.mock('@/services/youtubeService', () => ({
  youtubeService: {
    searchPlaylists: vi.fn(),
    getPlaylist: vi.fn(),
  },
}));

vi.mock('@/constants/defaultPlaylists', () => ({
  DEFAULT_PLAYLISTS: [
    {
      youtube_id: '1',
      name: 'Top France',
      description: 'Les meilleurs hits',
      image_url: null,
      category: 'Pop',
      owner: 'Deezer',
    },
  ],
  PLAYLIST_CATEGORIES: ['Tous', 'Pop', 'Rock'],
}));

vi.mock('@/components/ui', () => ({
  Alert: ({ children }: any) => <div data-testid="alert">{children}</div>,
  LoadingState: () => <div>Chargement...</div>,
  EmptyState: ({ title }: any) => <div>{title}</div>,
  Button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
}));

import PlaylistSelector from '@/components/playlist/PlaylistSelector';

class PlaylistSelectorTest {
  run() {
    describe('PlaylistSelector', () => {
      beforeEach(() => {
        vi.clearAllMocks();
      });

      this.testRendersDefaultPlaylists();
      this.testCategoryFilter();
      this.testSearchToggle();
      this.testSelectPlaylist();
    });
  }

  private testRendersDefaultPlaylists() {
    it('affiche les playlists par défaut', () => {
      render(<PlaylistSelector onSelectPlaylist={() => {}} />);
      expect(screen.getByText('Top France')).toBeInTheDocument();
      expect(screen.getByText('Playlists recommandées')).toBeInTheDocument();
    });
  }

  private testCategoryFilter() {
    it('filtre par catégorie', () => {
      render(<PlaylistSelector onSelectPlaylist={() => {}} />);
      expect(screen.getByText('Tous')).toBeInTheDocument();
      expect(screen.getByText('Pop')).toBeInTheDocument();
      expect(screen.getByText('Rock')).toBeInTheDocument();
    });
  }

  private testSearchToggle() {
    it('ouvre le champ de recherche', () => {
      render(<PlaylistSelector onSelectPlaylist={() => {}} />);
      fireEvent.click(screen.getByText(/Rechercher une playlist/));
      expect(screen.getByPlaceholderText(/Rechercher une playlist/)).toBeInTheDocument();
    });
  }

  private testSelectPlaylist() {
    it('appelle onSelectPlaylist au clic', () => {
      const onSelect = vi.fn();
      render(<PlaylistSelector onSelectPlaylist={onSelect} />);
      fireEvent.click(screen.getByText('Top France'));
      expect(onSelect).toHaveBeenCalled();
    });
  }
}

new PlaylistSelectorTest().run();
