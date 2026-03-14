import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AudioPlayerUI } from '@/components/game/AudioPlayerUI';

class AudioPlayerUITest {
  run() {
    describe('AudioPlayerUI', () => {
      this.testShowsPlayButton();
      this.testShowsPlayingState();
      this.testShowsError();
      this.testCompactMode();
      this.testCompactPlaying();
      this.testCompactError();
    });
  }

  private testShowsPlayButton() {
    it('affiche le bouton lancer la musique quand needsPlay', () => {
      render(
        <AudioPlayerUI
          isPlaying={false}
          needsPlay={true}
          playerError={null}
          handlePlay={() => {}}
        />,
      );
      expect(screen.getByText(/Lancer la musique/)).toBeInTheDocument();
    });
  }

  private testShowsPlayingState() {
    it("affiche l'état lecture en cours", () => {
      render(
        <AudioPlayerUI
          isPlaying={true}
          needsPlay={false}
          playerError={null}
          handlePlay={() => {}}
        />,
      );
      expect(screen.getByText(/Écoutez attentivement/)).toBeInTheDocument();
    });
  }

  private testShowsError() {
    it("affiche l'erreur et le bouton réessayer", () => {
      const handlePlay = vi.fn();
      render(
        <AudioPlayerUI
          isPlaying={false}
          needsPlay={false}
          playerError="Erreur audio"
          handlePlay={handlePlay}
        />,
      );
      expect(screen.getByText('Erreur audio')).toBeInTheDocument();
      fireEvent.click(screen.getByText(/Réessayer/));
      expect(handlePlay).toHaveBeenCalled();
    });
  }

  private testCompactMode() {
    it('affiche le bouton compact Écouter', () => {
      render(
        <AudioPlayerUI
          isPlaying={false}
          needsPlay={true}
          playerError={null}
          handlePlay={() => {}}
          compact
        />,
      );
      expect(screen.getByText(/Écouter/)).toBeInTheDocument();
    });
  }

  private testCompactPlaying() {
    it('affiche En écoute en mode compact', () => {
      render(
        <AudioPlayerUI
          isPlaying={true}
          needsPlay={false}
          playerError={null}
          handlePlay={() => {}}
          compact
        />,
      );
      expect(screen.getByText(/En écoute/)).toBeInTheDocument();
    });
  }

  private testCompactError() {
    it('affiche Réessayer en mode compact si erreur', () => {
      render(
        <AudioPlayerUI
          isPlaying={false}
          needsPlay={false}
          playerError="err"
          handlePlay={() => {}}
          compact
        />,
      );
      expect(screen.getByText(/Réessayer/)).toBeInTheDocument();
    });
  }
}

new AudioPlayerUITest().run();
