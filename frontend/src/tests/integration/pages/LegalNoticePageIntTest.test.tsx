import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { BasePageTest } from '../base/BasePageTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import LegalNoticePage from '@/pages/legal/LegalNoticePage';

class LegalNoticePageIntTest extends BasePageTest {
  protected getRoute() { return '/legal'; }
  protected getComponent() { return LegalNoticePage; }

  run() {
    describe('LegalNoticePage (intégration)', () => {
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
        expect(screen.getByText('Mentions légales')).toBeInTheDocument();
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

new LegalNoticePageIntTest().run();
