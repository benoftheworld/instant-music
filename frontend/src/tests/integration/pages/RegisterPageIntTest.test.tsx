import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { BaseFormTest } from '../base/BaseFormTest';
import { seedDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import RegisterPage from '@/pages/auth/RegisterPage';

class RegisterPageIntTest extends BaseFormTest {
  protected getRoute() { return '/register'; }
  protected getComponent() { return RegisterPage; }

  run() {
    describe('RegisterPage (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testRendersForm();
      this.testSuccessfulRegistration();
      this.testDuplicateUsername();
      this.testPrivacyCheckbox();
      this.testLoginLink();
    });
  }

  private testRendersForm() {
    it('affiche le formulaire d\'inscription', () => {
      this.renderPage();
      expect(screen.getByText('Inscription')).toBeInTheDocument();
      expect(screen.getByLabelText(/Nom d'utilisateur/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Email/)).toBeInTheDocument();
      expect(screen.getByLabelText('Mot de passe')).toBeInTheDocument();
      expect(screen.getByLabelText(/Confirmer/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /S'inscrire/ })).toBeInTheDocument();
    });
  }

  private testSuccessfulRegistration() {
    it('inscrit un nouvel utilisateur', async () => {
      const { user } = this.renderPage();
      await this.fillField(user, /Nom d'utilisateur/, 'newuser');
      await this.fillField(user, /Email/, 'new@test.com');
      await this.fillField(user, 'Mot de passe', 'StrongPass1!');
      await this.fillField(user, /Confirmer/, 'StrongPass1!');
      // Check privacy checkbox
      const checkbox = screen.getByLabelText(/politique de confidentialité/);
      await user.click(checkbox);
      await this.submitForm(user, "S'inscrire");

      await waitFor(() => {
        expect(screen.queryByText(/Erreur lors de l'inscription/)).not.toBeInTheDocument();
      });
    });
  }

  private testDuplicateUsername() {
    it('affiche une erreur si le pseudonyme est pris', async () => {
      const { user } = this.renderPage();
      await this.fillField(user, /Nom d'utilisateur/, 'alice');
      await this.fillField(user, /Email/, 'alice@test.com');
      await this.fillField(user, 'Mot de passe', 'StrongPass1!');
      await this.fillField(user, /Confirmer/, 'StrongPass1!');
      const checkbox = screen.getByLabelText(/politique de confidentialité/);
      await user.click(checkbox);
      await this.submitForm(user, "S'inscrire");

      await waitFor(() => {
        expect(screen.getByText(/Erreur lors de l'inscription/)).toBeInTheDocument();
      });
    });
  }

  private testPrivacyCheckbox() {
    it('affiche la case politique de confidentialité', () => {
      this.renderPage();
      expect(screen.getByLabelText(/politique de confidentialité/)).toBeInTheDocument();
    });
  }

  private testLoginLink() {
    it('affiche le lien vers la connexion', () => {
      this.renderPage();
      expect(screen.getByText(/Connectez-vous/)).toBeInTheDocument();
    });
  }
}

new RegisterPageIntTest().run();
