import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SiteBanner from '@/components/layout/SiteBanner';

class SiteBannerTest {
  run() {
    describe('SiteBanner', () => {
      beforeEach(() => sessionStorage.clear());

      this.testRendersMessage();
      this.testHiddenWhenDisabled();
      this.testDismissible();
    });
  }

  private testRendersMessage() {
    it('affiche le message de la bannière', () => {
      render(
        <SiteBanner banner={{ enabled: true, message: 'Mise à jour!', color: 'info', dismissible: false }} />,
      );
      expect(screen.getByText('Mise à jour!')).toBeInTheDocument();
    });
  }

  private testHiddenWhenDisabled() {
    it('n\'affiche rien si désactivé', () => {
      const { container } = render(
        <SiteBanner banner={{ enabled: false, message: 'X', color: 'info', dismissible: true }} />,
      );
      expect(container.innerHTML).toBe('');
    });
  }

  private testDismissible() {
    it('peut être fermée et persiste en sessionStorage', async () => {
      render(
        <SiteBanner banner={{ enabled: true, message: 'Bye', color: 'warning', dismissible: true }} />,
      );
      const closeButton = screen.getByLabelText('Fermer le bandeau');
      await userEvent.click(closeButton);
      expect(screen.queryByText('Bye')).not.toBeInTheDocument();
    });
  }
}

new SiteBannerTest().run();
