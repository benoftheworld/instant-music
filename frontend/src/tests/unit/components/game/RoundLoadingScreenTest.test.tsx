import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('@/services/soundEffects', () => ({
  soundEffects: { countdownBeep: vi.fn(), countdownGo: vi.fn() },
}));

import RoundLoadingScreen from '@/components/game/RoundLoadingScreen';

class RoundLoadingScreenTest {
  run() {
    describe('RoundLoadingScreen', () => {
      this.testRendersRoundNumber();
      this.testRendersCountdown();
    });
  }

  private testRendersRoundNumber() {
    it('affiche le numéro de round', () => {
      render(<RoundLoadingScreen roundNumber={3} onComplete={vi.fn()} duration={5} />);
      expect(screen.getByText(/Round 3/)).toBeInTheDocument();
    });
  }

  private testRendersCountdown() {
    it('affiche "Préparez-vous"', () => {
      render(<RoundLoadingScreen roundNumber={1} onComplete={vi.fn()} />);
      expect(screen.getByText('Préparez-vous !')).toBeInTheDocument();
    });
  }
}

new RoundLoadingScreenTest().run();
