import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Button from '@/components/ui/Button';

class ButtonTest {
  run() {
    describe('Button', () => {
      this.testRendersChildren();
      this.testVariants();
      this.testSizes();
      this.testLoading();
      this.testDisabled();
      this.testIcon();
      this.testOnClick();
    });
  }

  private testRendersChildren() {
    it('affiche le texte enfant', () => {
      render(<Button>Cliquer</Button>);
      expect(screen.getByText('Cliquer')).toBeInTheDocument();
    });
  }

  private testVariants() {
    it.each(['primary', 'secondary', 'outline', 'ghost', 'danger'] as const)(
      'variant %s — rend un bouton',
      (variant) => {
        render(<Button variant={variant}>V</Button>);
        expect(screen.getByRole('button')).toBeInTheDocument();
      },
    );
  }

  private testSizes() {
    it.each(['sm', 'md', 'lg'] as const)('size %s — rend sans erreur', (size) => {
      render(<Button size={size}>S</Button>);
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
  }

  private testLoading() {
    it('loading — désactive le bouton', () => {
      render(<Button loading>Wait</Button>);
      expect(screen.getByRole('button')).toBeDisabled();
    });
  }

  private testDisabled() {
    it('disabled — désactive le bouton', () => {
      render(<Button disabled>Nope</Button>);
      expect(screen.getByRole('button')).toBeDisabled();
    });
  }

  private testIcon() {
    it('affiche une icône si fournie', () => {
      render(<Button icon={<span data-testid="ico">I</span>}>Ok</Button>);
      expect(screen.getByTestId('ico')).toBeInTheDocument();
    });
  }

  private testOnClick() {
    it('appelle onClick au clic', async () => {
      const handler = vi.fn();
      render(<Button onClick={handler}>Click</Button>);
      await userEvent.click(screen.getByRole('button'));
      expect(handler).toHaveBeenCalledOnce();
    });
  }
}

new ButtonTest().run();
