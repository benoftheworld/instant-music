import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Badge from '@/components/ui/Badge';

class BadgeTest {
  run() {
    describe('Badge', () => {
      this.testRendersChildren();
      this.testVariants();
      this.testIcon();
      this.testSizes();
    });
  }

  private testRendersChildren() {
    it('affiche le texte enfant', () => {
      render(<Badge>Nouveau</Badge>);
      expect(screen.getByText('Nouveau')).toBeInTheDocument();
    });
  }

  private testVariants() {
    it.each(['default', 'primary', 'success', 'warning', 'danger', 'info'] as const)(
      'variant %s — rend sans erreur',
      (variant) => {
        const { container } = render(<Badge variant={variant}>V</Badge>);
        expect(container.firstChild).toBeTruthy();
      },
    );
  }

  private testIcon() {
    it('affiche une icône si fournie', () => {
      render(<Badge icon={<span data-testid="icon">★</span>}>Star</Badge>);
      expect(screen.getByTestId('icon')).toBeInTheDocument();
    });
  }

  private testSizes() {
    it.each(['sm', 'md'] as const)('size %s — rend sans erreur', (size) => {
      const { container } = render(<Badge size={size}>S</Badge>);
      expect(container.firstChild).toBeTruthy();
    });
  }
}

new BadgeTest().run();
