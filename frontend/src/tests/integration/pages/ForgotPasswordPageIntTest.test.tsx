import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { BaseFormTest } from '../base/BaseFormTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import ForgotPasswordPage from '@/pages/auth/ForgotPasswordPage';

class ForgotPasswordPageIntTest extends BaseFormTest {
  protected getRoute() { return '/forgot-password'; }
  protected getComponent() { return ForgotPasswordPage; }

  run() {
    describe('ForgotPasswordPage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersForm();
      this.testSubmitUsername();
      this.testSubmitEmail();
      this.testBackToLoginLink();
    });
  }

  private testRendersForm() {
    it('affiche le formulaire de réinitialisation avec un champ pseudonyme ou email', () => {
      this.renderPage();
      expect(screen.getByText('Mot de passe oublié')).toBeInTheDocument();
      expect(screen.getByLabelText(/Pseudonyme ou email/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Envoyer le lien/ })).toBeInTheDocument();
    });
  }

  private testSubmitUsername() {
    it('affiche la confirmation après soumission du pseudonyme', async () => {
      const { user } = this.renderPage();
      await this.fillField(user, /Pseudonyme ou email/, 'alice');
      await this.submitForm(user, 'Envoyer le lien');

      await waitFor(() => {
        expect(screen.getByText(/un lien de réinitialisation vous a été envoyé/)).toBeInTheDocument();
      });
    });
  }

  private testSubmitEmail() {
    it('affiche la confirmation après soumission d\'une adresse email', async () => {
      const { user } = this.renderPage();
      await this.fillField(user, /Pseudonyme ou email/, 'alice@exemple.com');
      await this.submitForm(user, 'Envoyer le lien');

      await waitFor(() => {
        expect(screen.getByText(/un lien de réinitialisation vous a été envoyé/)).toBeInTheDocument();
      });
    });
  }

  private testBackToLoginLink() {
    it('affiche le lien retour à la connexion', () => {
      this.renderPage();
      expect(screen.getByText(/Retour à la connexion/)).toBeInTheDocument();
    });
  }
}

new ForgotPasswordPageIntTest().run();
