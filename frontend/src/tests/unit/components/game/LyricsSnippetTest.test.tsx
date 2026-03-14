import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import LyricsSnippet from '@/components/game/LyricsSnippet';

class LyricsSnippetTest {
  run() {
    describe('LyricsSnippet', () => {
      this.testRendersSnippetWithBlank();
      this.testShowsQuestionMarks();
      this.testShowsCorrectAnswer();
    });
  }

  private testRendersSnippetWithBlank() {
    it('affiche le snippet avec un trou', () => {
      render(
        <LyricsSnippet snippet="Is this the real _____" showAnswer={false} />,
      );
      expect(screen.getByText('Is this the real')).toBeInTheDocument();
      expect(screen.getByText('???')).toBeInTheDocument();
    });
  }

  private testShowsQuestionMarks() {
    it('affiche ??? quand showAnswer est false', () => {
      render(
        <LyricsSnippet
          snippet="Hello _____ my old friend"
          correctAnswer="darkness"
          showAnswer={false}
        />,
      );
      expect(screen.getByText('???')).toBeInTheDocument();
      expect(screen.queryByText('darkness')).not.toBeInTheDocument();
    });
  }

  private testShowsCorrectAnswer() {
    it('affiche la bonne réponse quand showAnswer est true', () => {
      render(
        <LyricsSnippet
          snippet="Hello _____ my old friend"
          correctAnswer="darkness"
          showAnswer={true}
        />,
      );
      expect(screen.getByText('darkness')).toBeInTheDocument();
      expect(screen.queryByText('???')).not.toBeInTheDocument();
    });
  }
}

new LyricsSnippetTest().run();
