import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { OptionsGrid } from '@/components/game/OptionsGrid';

vi.mock('@/services/soundEffects', () => ({
  soundEffects: { click: vi.fn() },
}));

class OptionsGridTest {
  private options = ['Beatles', 'Queen', 'ABBA', 'Nirvana'];

  run() {
    describe('OptionsGrid', () => {
      this.testRendersAllOptions();
      this.testClickCallsOnOptionClick();
      this.testDisabledAfterAnswer();
      this.testExcludedHidden();
      this.testCorrectAnswerHighlighted();
    });
  }

  private testRendersAllOptions() {
    it('affiche toutes les options', () => {
      render(
        <OptionsGrid
          options={this.options}
          hasAnswered={false}
          showResults={false}
          selectedAnswer={null}
          roundResults={null}
          onOptionClick={vi.fn()}
        />,
      );
      for (const opt of this.options) {
        expect(screen.getByText(opt)).toBeInTheDocument();
      }
    });
  }

  private testClickCallsOnOptionClick() {
    it('clic appelle onOptionClick avec l\'option', async () => {
      const handler = vi.fn();
      render(
        <OptionsGrid
          options={this.options}
          hasAnswered={false}
          showResults={false}
          selectedAnswer={null}
          roundResults={null}
          onOptionClick={handler}
        />,
      );
      await userEvent.click(screen.getByText('Queen'));
      expect(handler).toHaveBeenCalledWith('Queen');
    });
  }

  private testDisabledAfterAnswer() {
    it('boutons désactivés après réponse', () => {
      render(
        <OptionsGrid
          options={this.options}
          hasAnswered={true}
          showResults={false}
          selectedAnswer="Queen"
          roundResults={null}
          onOptionClick={vi.fn()}
        />,
      );
      const buttons = screen.getAllByRole('button');
      buttons.forEach((btn) => expect(btn).toBeDisabled());
    });
  }

  private testExcludedHidden() {
    it('options exclues sont masquées', () => {
      render(
        <OptionsGrid
          options={this.options}
          hasAnswered={false}
          showResults={false}
          selectedAnswer={null}
          roundResults={null}
          onOptionClick={vi.fn()}
          excludedOptions={['ABBA']}
        />,
      );
      expect(screen.queryByText('ABBA')).not.toBeInTheDocument();
    });
  }

  private testCorrectAnswerHighlighted() {
    it('bonne réponse mise en évidence en mode résultat', () => {
      render(
        <OptionsGrid
          options={this.options}
          hasAnswered={true}
          showResults={true}
          selectedAnswer="Queen"
          roundResults={{ correct_answer: 'Beatles' }}
          onOptionClick={vi.fn()}
        />,
      );
      // Beatles button should have green class, Queen should have red
      const beatlesBtn = screen.getByText('Beatles').closest('button');
      expect(beatlesBtn?.className).toContain('green');
      const queenBtn = screen.getByText('Queen').closest('button');
      expect(queenBtn?.className).toContain('red');
    });
  }
}

new OptionsGridTest().run();
