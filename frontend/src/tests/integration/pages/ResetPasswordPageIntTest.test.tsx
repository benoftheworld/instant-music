import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { BaseFormTest } from '../base/BaseFormTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import ResetPasswordPage from '@/pages/auth/ResetPasswordPage';

class ResetPasswordPageIntTest extends BaseFormTest {
  protected getRoute() { return '/reset-password/:uid/:token'; }
  protected getComponent() { return ResetPasswordPage; }

  run() {
    describe('ResetPasswordPage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersForm();
      this.testMismatchedPasswords();
      this.testSuccessfulReset();
    });
  }

  private testRendersForm() {
    it('affiche le formulaire de nouveau mot de passe', () => {
      this.renderPage(['/reset-password/abc123/token456']);
      expect(screen.getByText('Nouveau mot de passe')).toBeInTheDocument();
      expect(screen.getByLabelText(/Nouveau mot de passe/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Confirmer/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Réinitialiser/ })).toBeInTheDocument();
    });
  }

  private testMismatchedPasswords() {
    it('affiche une erreur si les mots de passe ne correspondent pas', async () => {
      const { user } = this.renderPage(['/reset-password/abc123/token456']);
      await this.fillField(user, /Nouveau mot de passe/, 'NewPass123!');
      await this.fillField(user, /Confirmer/, 'DifferentPass!');
      await this.submitForm(user, 'Réinitialiser');

      await waitFor(() => {
        expect(screen.getByText(/Les mots de passe ne correspondent pas/)).toBeInTheDocument();
      });
    });
  }

  private testSuccessfulReset() {
    it('réinitialise le mot de passe avec succès', async () => {
      const { user } = this.renderPage(['/reset-password/abc123/token456']);
      await this.fillField(user, /Nouveau mot de passe/, 'NewPass123!');
      await this.fillField(user, /Confirmer/, 'NewPass123!');
      await this.submitForm(user, 'Réinitialiser');

      // After success, it navigates to /login — no error should be shown
      await waitFor(() => {
        expect(screen.queryByText(/Lien invalide ou expiré/)).not.toBeInTheDocument();
      });
    });
  }
}

new ResetPasswordPageIntTest().run();
