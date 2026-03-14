import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TextAnswerInput from '@/components/game/TextAnswerInput';

class TextAnswerInputTest {
  run() {
    describe('TextAnswerInput', () => {
      this.testRendersInput();
      this.testSubmitOnClick();
      this.testSubmitDisabledIfEmpty();
      this.testShowsSelectedAnswer();
      this.testShowsResults();
    });
  }

  private testRendersInput() {
    it('affiche un champ de saisie et bouton Valider', () => {
      render(
        <TextAnswerInput
          onSubmit={vi.fn()}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByPlaceholderText('Tapez votre réponse...')).toBeInTheDocument();
      expect(screen.getByText('Valider')).toBeInTheDocument();
    });
  }

  private testSubmitOnClick() {
    it('appelle onSubmit au clic sur Valider', async () => {
      const handler = vi.fn();
      render(
        <TextAnswerInput
          onSubmit={handler}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      await userEvent.type(screen.getByPlaceholderText('Tapez votre réponse...'), 'Beatles');
      await userEvent.click(screen.getByText('Valider'));
      expect(handler).toHaveBeenCalledWith('Beatles');
    });
  }

  private testSubmitDisabledIfEmpty() {
    it('bouton Valider désactivé si vide', () => {
      render(
        <TextAnswerInput
          onSubmit={vi.fn()}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('Valider')).toBeDisabled();
    });
  }

  private testShowsSelectedAnswer() {
    it('affiche la réponse sélectionnée en attente', () => {
      render(
        <TextAnswerInput
          onSubmit={vi.fn()}
          hasAnswered={true}
          selectedAnswer="Beatles"
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText(/Beatles/)).toBeInTheDocument();
      expect(screen.getByText(/En attente/i)).toBeInTheDocument();
    });
  }

  private testShowsResults() {
    it('affiche la bonne réponse en mode résultat', () => {
      render(
        <TextAnswerInput
          onSubmit={vi.fn()}
          hasAnswered={true}
          selectedAnswer="Queen"
          showResults={true}
          roundResults={{ correct_answer: 'Beatles', points_earned: 0 }}
        />,
      );
      expect(screen.getByText(/Beatles/)).toBeInTheDocument();
      expect(screen.getByText(/Dommage/i)).toBeInTheDocument();
    });
  }
}

new TextAnswerInputTest().run();
