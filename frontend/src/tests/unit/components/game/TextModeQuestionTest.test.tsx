import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { GameRound } from '@/components/game/types';

vi.mock('@/components/game/useAudioPlayer', () => ({
  useAudioPlayer: () => ({
    isPlaying: false,
    needsPlay: false,
    playerError: null,
    handlePlay: vi.fn(),
  }),
  useAudioPlayerOnResults: () => ({
    isPlaying: false,
    needsPlay: false,
    playerError: null,
    handlePlay: vi.fn(),
  }),
}));

import TextModeQuestion from '@/components/game/TextModeQuestion';

function makeRound(overrides: Partial<GameRound> = {}): GameRound {
  return {
    round_number: 1,
    track_name: 'Track',
    artist_name: 'Artist',
    preview_url: 'http://example.com/p.mp3',
    duration: 30,
    options: [],
    question_type: 'quiz',
    question_text: 'Quel est le titre ?',
    extra_data: {},
    ...overrides,
  } as GameRound;
}

class TextModeQuestionTest {
  run() {
    describe('TextModeQuestion', () => {
      this.testRendersQuestionText();
      this.testRendersInput();
      this.testLyricsModeSnippet();
    });
  }

  private testRendersQuestionText() {
    it('affiche le texte de la question', () => {
      render(
        <TextModeQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('Quel est le titre ?')).toBeInTheDocument();
    });
  }

  private testRendersInput() {
    it("affiche l'input de saisie libre", () => {
      render(
        <TextModeQuestion
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });
  }

  private testLyricsModeSnippet() {
    it('affiche le snippet en mode lyrics', () => {
      render(
        <TextModeQuestion
          round={makeRound({
            question_type: 'lyrics',
            extra_data: { lyrics_snippet: 'Hello _____ my old friend' },
          })}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('???')).toBeInTheDocument();
    });
  }
}

new TextModeQuestionTest().run();
