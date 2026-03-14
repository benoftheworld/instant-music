import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ResultFooter } from '@/components/game/ResultFooter';
import type { RoundResults } from '@/components/game/types';

class ResultFooterTest {
  run() {
    describe('ResultFooter', () => {
      this.testWaitingMessage();
      this.testCorrectAnswer();
      this.testWrongAnswer();
      this.testNoRender();
    });
  }

  private testWaitingMessage() {
    it('affiche "En attente" si répondu mais pas encore résultats', () => {
      render(
        <ResultFooter
          showResults={false}
          roundResults={null}
          selectedAnswer="Queen"
          hasAnswered={true}
        />,
      );
      expect(screen.getByText(/En attente des autres joueurs/)).toBeInTheDocument();
    });
  }

  private testCorrectAnswer() {
    it('affiche Bravo si bonne réponse', () => {
      const results: RoundResults = { correct_answer: 'Queen', points_earned: 100 };
      render(
        <ResultFooter
          showResults={true}
          roundResults={results}
          selectedAnswer="Queen"
          hasAnswered={true}
        />,
      );
      expect(screen.getByText(/Bravo/)).toBeInTheDocument();
      expect(screen.getByText(/\+100 points/)).toBeInTheDocument();
    });
  }

  private testWrongAnswer() {
    it('affiche Dommage si mauvaise réponse', () => {
      const results: RoundResults = { correct_answer: 'Queen', points_earned: 0 };
      render(
        <ResultFooter
          showResults={true}
          roundResults={results}
          selectedAnswer="Beatles"
          hasAnswered={true}
        />,
      );
      expect(screen.getByText(/Dommage/)).toBeInTheDocument();
    });
  }

  private testNoRender() {
    it('ne rend rien si pas répondu et pas de résultats', () => {
      const { container } = render(
        <ResultFooter
          showResults={false}
          roundResults={null}
          selectedAnswer={null}
          hasAnswered={false}
        />,
      );
      expect(container.textContent).toBe('');
    });
  }
}

new ResultFooterTest().run();
