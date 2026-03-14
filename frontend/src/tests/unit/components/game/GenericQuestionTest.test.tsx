import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { GameRound } from '@/components/game/types';

// Mock the audio hook and shared components
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

import GenericQuestion from '@/components/game/GenericQuestion';

function makeRound(overrides: Partial<GameRound> = {}): GameRound {
  return {
    round_number: 1,
    track_name: 'Track',
    artist_name: 'Artist',
    preview_url: 'http://example.com/preview.mp3',
    duration: 30,
    options: ['A', 'B', 'C', 'D'],
    question_type: 'quiz',
    question_text: '',
    extra_data: {},
    ...overrides,
  } as GameRound;
}

class GenericQuestionTest {
  run() {
    describe('GenericQuestion', () => {
      this.testRendersIconAndTitle();
      this.testRenders4Options();
      this.testSubtitle();
    });
  }

  private testRendersIconAndTitle() {
    it("affiche l'icône et le titre par défaut", () => {
      render(
        <GenericQuestion
          icon="🎵"
          defaultTitle="Quel est le titre ?"
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('🎵')).toBeInTheDocument();
      expect(screen.getByText('Quel est le titre ?')).toBeInTheDocument();
    });
  }

  private testRenders4Options() {
    it('affiche les 4 options', () => {
      render(
        <GenericQuestion
          icon="🎵"
          defaultTitle="Titre ?"
          round={makeRound({ options: ['Option Alpha', 'Option Beta', 'Option Gamma', 'Option Delta'] })}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('Option Alpha')).toBeInTheDocument();
      expect(screen.getByText('Option Beta')).toBeInTheDocument();
      expect(screen.getByText('Option Gamma')).toBeInTheDocument();
      expect(screen.getByText('Option Delta')).toBeInTheDocument();
    });
  }

  private testSubtitle() {
    it('affiche le sous-titre si fourni', () => {
      render(
        <GenericQuestion
          icon="🎵"
          defaultTitle="Titre ?"
          subtitle="Un indice"
          round={makeRound()}
          onAnswerSubmit={() => {}}
          hasAnswered={false}
          selectedAnswer={null}
          showResults={false}
          roundResults={null}
        />,
      );
      expect(screen.getByText('Un indice')).toBeInTheDocument();
    });
  }
}

new GenericQuestionTest().run();
