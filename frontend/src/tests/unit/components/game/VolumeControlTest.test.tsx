import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

vi.mock('@/services/soundEffects', () => ({
  soundEffects: {
    isEnabled: vi.fn(() => true),
    getVolume: vi.fn(() => 0.8),
    setEnabled: vi.fn(),
    setVolume: vi.fn(),
  },
}));

import VolumeControl from '@/components/game/VolumeControl';

class VolumeControlTest {
  run() {
    describe('VolumeControl', () => {
      beforeEach(() => {
        vi.clearAllMocks();
        localStorage.clear();
      });

      this.testFloatingRenders();
      this.testFloatingOpenClose();
      this.testCardRenders();
      this.testMuteToggle();
    });
  }

  private testFloatingRenders() {
    it('affiche le bouton flottant par défaut', () => {
      render(<VolumeControl />);
      expect(screen.getByTitle('Réglages du son')).toBeInTheDocument();
    });
  }

  private testFloatingOpenClose() {
    it('ouvre le popup au clic sur le bouton flottant', () => {
      render(<VolumeControl />);
      fireEvent.click(screen.getByTitle('Réglages du son'));
      expect(screen.getByText('Volume')).toBeInTheDocument();
    });
  }

  private testCardRenders() {
    it('affiche le variant card avec les sliders', () => {
      render(<VolumeControl variant="card" />);
      expect(screen.getByText('Réglages du son')).toBeInTheDocument();
      expect(screen.getByText('Effets sonores')).toBeInTheDocument();
      expect(screen.getByText('Volume musique')).toBeInTheDocument();
    });
  }

  private testMuteToggle() {
    it('toggle le mute au clic sur le bouton Son activé', () => {
      render(<VolumeControl variant="card" />);
      const toggleBtn = screen.getByText('Son activé').closest('div')!.querySelector('button')!;
      fireEvent.click(toggleBtn);
      // After mute, the effects slider should be disabled
      const sliders = screen.getAllByRole('slider');
      expect(sliders[0]).toBeDisabled();
    });
  }
}

new VolumeControlTest().run();
