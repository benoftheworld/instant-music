import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Alert from '@/components/ui/Alert';

class AlertTest {
  run() {
    describe('Alert', () => {
      this.testRendersChildren();
      this.testVariants();
      this.testCloseButton();
      this.testCustomIcon();
      this.testRoleAlert();
    });
  }

  private testRendersChildren() {
    it('affiche le contenu enfant', () => {
      render(<Alert variant="info">Hello world</Alert>);
      expect(screen.getByText('Hello world')).toBeInTheDocument();
    });
  }

  private testVariants() {
    it.each(['success', 'error', 'warning', 'info'] as const)(
      'variant %s — affiche l\'icône par défaut',
      (variant) => {
        render(<Alert variant={variant}>msg</Alert>);
        expect(screen.getByRole('alert')).toBeInTheDocument();
      },
    );
  }

  private testCloseButton() {
    it('affiche un bouton fermer si onClose fourni', async () => {
      const onClose = vi.fn();
      render(<Alert variant="info" onClose={onClose}>msg</Alert>);
      await userEvent.click(screen.getByLabelText('Fermer'));
      expect(onClose).toHaveBeenCalledOnce();
    });
  }

  private testCustomIcon() {
    it('affiche une icône custom si fournie', () => {
      render(<Alert variant="success" icon={<span data-testid="custom">X</span>}>msg</Alert>);
      expect(screen.getByTestId('custom')).toBeInTheDocument();
    });
  }

  private testRoleAlert() {
    it('a le rôle alert', () => {
      render(<Alert variant="error">err</Alert>);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  }
}

import { vi } from 'vitest';
new AlertTest().run();
