import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QuestionHeader } from '@/components/game/QuestionHeader';

class QuestionHeaderTest {
  run() {
    describe('QuestionHeader', () => {
      this.testRendersIconAndTitle();
      this.testRendersSubtitle();
      this.testRendersBadge();
    });
  }

  private testRendersIconAndTitle() {
    it('affiche l\'icône et le titre', () => {
      render(<QuestionHeader icon="🎵" title="Round 1" />);
      expect(screen.getByText('🎵')).toBeInTheDocument();
      expect(screen.getByText('Round 1')).toBeInTheDocument();
    });
  }

  private testRendersSubtitle() {
    it('affiche le sous-titre si fourni', () => {
      render(<QuestionHeader icon="🎵" title="T" subtitle="Classique" />);
      expect(screen.getByText('Classique')).toBeInTheDocument();
    });
  }

  private testRendersBadge() {
    it('affiche le badge si fourni', () => {
      render(<QuestionHeader icon="🎵" title="T" badge={<span data-testid="badge">B</span>} />);
      expect(screen.getByTestId('badge')).toBeInTheDocument();
    });
  }
}

new QuestionHeaderTest().run();
