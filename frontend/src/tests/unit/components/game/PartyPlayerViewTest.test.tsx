import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PartyPlayerView from '@/components/game/PartyPlayerView';

function makeRound(overrides = {}) {
  return {
    round_number: 3,
    track_name: 'Track',
    artist_name: 'Artist',
    preview_url: 'http://example.com/p.mp3',
    duration: 30,
    options: ['Opt A', 'Opt B', 'Opt C', 'Opt D'],
    question_type: 'quiz',
    question_text: '',
    extra_data: {},
    ...overrides,
  } as any;
}

class PartyPlayerViewTest {
  run() {
    describe('PartyPlayerView', () => {
      this.testMcqRendersOptions();
      this.testMcqClickSubmits();
      this.testTextModeInput();
      this.testAnsweredState();
      this.testResultsCorrect();
      this.testResultsWrong();
    });
  }

  private testMcqRendersOptions() {
    it('affiche les boutons QCM en mode mcq', () => {
      render(
        <PartyPlayerView
          round={makeRound()}
          timeRemaining={20}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
          answerMode="mcq"
          onAnswerSubmit={() => {}}
        />,
      );
      expect(screen.getByText('Opt A')).toBeInTheDocument();
      expect(screen.getByText('Opt D')).toBeInTheDocument();
      expect(screen.getByText('Manche 3')).toBeInTheDocument();
    });
  }

  private testMcqClickSubmits() {
    it('soumet la réponse au clic sur une option', () => {
      const onSubmit = vi.fn();
      render(
        <PartyPlayerView
          round={makeRound()}
          timeRemaining={20}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
          answerMode="mcq"
          onAnswerSubmit={onSubmit}
        />,
      );
      fireEvent.click(screen.getByText('Opt B'));
      expect(onSubmit).toHaveBeenCalledWith('Opt B');
    });
  }

  private testTextModeInput() {
    it('affiche le champ de saisie en mode texte', () => {
      render(
        <PartyPlayerView
          round={makeRound({ question_type: 'guess_artist' })}
          timeRemaining={20}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
          answerMode="text"
          onAnswerSubmit={() => {}}
        />,
      );
      expect(screen.getByPlaceholderText('Votre réponse…')).toBeInTheDocument();
    });
  }

  private testAnsweredState() {
    it('affiche "Réponse envoyée" après avoir répondu', () => {
      render(
        <PartyPlayerView
          round={makeRound()}
          timeRemaining={15}
          hasAnswered={true}
          selectedAnswer="Opt A"
          showResults={false}
          roundResults={null}
          answerMode="mcq"
          onAnswerSubmit={() => {}}
        />,
      );
      expect(screen.getByText(/Réponse envoyée/)).toBeInTheDocument();
    });
  }

  private testResultsCorrect() {
    it('affiche "Bonne réponse" si correct', () => {
      render(
        <PartyPlayerView
          round={makeRound()}
          timeRemaining={0}
          hasAnswered={true}
          selectedAnswer="Opt A"
          showResults={true}
          roundResults={{ correct_answer: 'Opt A', points_earned: 100 }}
          answerMode="mcq"
          onAnswerSubmit={() => {}}
          myPointsEarned={100}
        />,
      );
      expect(screen.getByText(/Bonne réponse/)).toBeInTheDocument();
      expect(screen.getByText(/\+100 pts/)).toBeInTheDocument();
    });
  }

  private testResultsWrong() {
    it('affiche "Mauvaise réponse" si incorrect', () => {
      render(
        <PartyPlayerView
          round={makeRound()}
          timeRemaining={0}
          hasAnswered={true}
          selectedAnswer="Opt B"
          showResults={true}
          roundResults={{ correct_answer: 'Opt A', points_earned: 0 }}
          answerMode="mcq"
          onAnswerSubmit={() => {}}
        />,
      );
      expect(screen.getByText(/Mauvaise réponse/)).toBeInTheDocument();
    });
  }
}

new PartyPlayerViewTest().run();
