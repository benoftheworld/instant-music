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
      this.testPasswordEyeToggle();
      this.testPasswordStrengthBar();
      this.testPasswordPlaceholders();
      this.testKeePassTip();
    });
  }

  private testRendersForm() {
    it('affiche le formulaire de nouveau mot de passe', () => {
      this.renderPage(['/reset-password/abc123/token456']);
      expect(screen.getByRole('heading', { name: /Nouveau mot de passe/ })).toBeInTheDocument();
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

  private testPasswordEyeToggle() {
    it('permet d\'afficher/masquer le mot de passe via l\'icône œil', async () => {
      const { user } = this.renderPage(['/reset-password/abc123/token456']);
      const passwordInput = screen.getByLabelText(/Nouveau mot de passe/);
      expect(passwordInput).toHaveAttribute('type', 'password');

      const toggleBtn = screen.getAllByRole('button', { name: /Afficher le mot de passe/i })[0];
      await user.click(toggleBtn);
      expect(passwordInput).toHaveAttribute('type', 'text');

      await user.click(screen.getAllByRole('button', { name: /Masquer le mot de passe/i })[0]);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });
  }

  private testPasswordStrengthBar() {
    it('affiche la barre de force du mot de passe lors de la saisie', async () => {
      const { user } = this.renderPage(['/reset-password/abc123/token456']);
      const passwordInput = screen.getByLabelText(/Nouveau mot de passe/);
      await user.type(passwordInput, 'StrongP@ss1!');

      await waitFor(() => {
        expect(screen.getByText(/Force/)).toBeInTheDocument();
      });
    });
  }

  private testPasswordPlaceholders() {
    it('affiche des placeholders décrivant les règles du mot de passe', () => {
      this.renderPage(['/reset-password/abc123/token456']);
      expect(screen.getByPlaceholderText(/8\+ car\./i)).toBeInTheDocument();
    });
  }

  private testKeePassTip() {
    it('affiche le conseil KeePass', () => {
      this.renderPage(['/reset-password/abc123/token456']);
      expect(screen.getByText(/KeePass/)).toBeInTheDocument();
    });
  }
}

new ResetPasswordPageIntTest().run();
