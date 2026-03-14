import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB, getDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import PrivacyPage from '@/pages/legal/PrivacyPage';

class PrivacyPageIntTest extends BasePageTest {
  protected getRoute() { return '/privacy'; }
  protected getComponent() { return PrivacyPage; }

  run() {
    describe('PrivacyPage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersLoading();
      this.testRendersContent();
      this.testRendersBackLink();
    });
  }

  private testRendersLoading() {
    it('affiche le chargement', () => {
      this.renderPage();
      expect(screen.getByText(/Chargement/)).toBeInTheDocument();
    });
  }

  private testRendersContent() {
    it('affiche le contenu après chargement', async () => {
      this.renderPage();
      await waitFor(() => {
        expect(screen.getByText('Politique de confidentialité')).toBeInTheDocument();
      });
    });
  }

  private testRendersBackLink() {
    it('affiche le lien retour', () => {
      this.renderPage();
      expect(screen.getByText(/Retour à l'accueil/)).toBeInTheDocument();
    });
  }
}

new PrivacyPageIntTest().run();
