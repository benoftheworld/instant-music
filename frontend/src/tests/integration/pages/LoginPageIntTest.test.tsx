import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { BaseFormTest } from '../base/BaseFormTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import LoginPage from '@/pages/auth/LoginPage';

class LoginPageIntTest extends BaseFormTest {
  protected getRoute() { return '/login'; }
  protected getComponent() { return LoginPage; }

  run() {
    describe('LoginPage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersForm();
      this.testSuccessfulLogin();
      this.testInvalidCredentials();
      this.testForgotPasswordLink();
      this.testRegisterLink();
    });
  }

  private testRendersForm() {
    it('affiche le formulaire de connexion', () => {
      this.renderPage();
      expect(screen.getByText('Connexion')).toBeInTheDocument();
      expect(screen.getByLabelText(/Identifiant/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Mot de passe/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Se connecter/ })).toBeInTheDocument();
    });
  }

  private testSuccessfulLogin() {
    it('connecte un utilisateur avec des identifiants valides', async () => {
      const { user } = this.renderPage();
      await this.fillField(user, /Identifiant/, 'alice');
      await this.fillField(user, /Mot de passe/, 'password123');
      await this.submitForm(user, 'Se connecter');

      // No error should appear after successful login
      await waitFor(() => {
        expect(screen.queryByText(/Identifiants invalides/)).not.toBeInTheDocument();
      });
    });
  }

  private testInvalidCredentials() {
    it('affiche une erreur avec des identifiants invalides', async () => {
      const { user } = this.renderPage();
      await this.fillField(user, /Identifiant/, 'unknown_user');
      await this.fillField(user, /Mot de passe/, 'wrong');
      await this.submitForm(user, 'Se connecter');

      await waitFor(() => {
        expect(screen.getByText(/Identifiants invalides/)).toBeInTheDocument();
      });
    });
  }

  private testForgotPasswordLink() {
    it('affiche le lien mot de passe oublié', () => {
      this.renderPage();
      expect(screen.getByText(/Mot de passe oublié/)).toBeInTheDocument();
    });
  }

  private testRegisterLink() {
    it('affiche le lien d\'inscription', () => {
      this.renderPage();
      expect(screen.getByText(/Inscrivez-vous/)).toBeInTheDocument();
    });
  }
}

new LoginPageIntTest().run();
