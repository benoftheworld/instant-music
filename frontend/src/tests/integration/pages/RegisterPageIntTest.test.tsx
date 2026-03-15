import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
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
      this.testUsernameTooLong();
      this.testEmailTooLong();
      this.testPasswordEyeToggle();
      this.testPasswordStrengthBar();
      this.testPasswordPlaceholders();
      this.testKeePassTip();
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
      const usernameInput = screen.getByLabelText(/Nom d'utilisateur/);
      await user.type(usernameInput, 'alice');
      // Trigger blur to fire availability check
      await user.tab();

      await waitFor(() => {
        expect(screen.getByText(/Ce pseudonyme est déjà utilisé/)).toBeInTheDocument();
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

  private testUsernameTooLong() {
    it('affiche une erreur si le pseudonyme dépasse 20 caractères', async () => {
      this.renderPage();
      const input = screen.getByLabelText(/Nom d'utilisateur/);
      // fireEvent bypasses the maxLength HTML attribute to test JS validation
      fireEvent.change(input, { target: { name: 'username', value: 'a'.repeat(21) } });

      await waitFor(() => {
        expect(screen.getByText(/ne peut pas dépasser 20 caractères/)).toBeInTheDocument();
      });
    });
  }

  private testEmailTooLong() {
    it('affiche une erreur si l\'email dépasse 50 caractères', async () => {
      this.renderPage();
      const input = screen.getByLabelText(/Email/);
      // fireEvent bypasses the maxLength HTML attribute to test JS validation
      fireEvent.change(input, { target: { name: 'email', value: 'a'.repeat(40) + '@example.com' } });

      await waitFor(() => {
        expect(screen.getByText(/ne peut pas dépasser 50 caractères/)).toBeInTheDocument();
      });
    });
  }

  private testPasswordEyeToggle() {
    it('permet d\'afficher/masquer le mot de passe via l\'icône œil', async () => {
      const { user } = this.renderPage();
      const passwordInput = screen.getByLabelText('Mot de passe');
      expect(passwordInput).toHaveAttribute('type', 'password');

      // Both password fields have eye-toggle buttons; take the first one
      const toggleBtns = screen.getAllByRole('button', { name: /Afficher le mot de passe/i });
      await user.click(toggleBtns[0]);
      expect(passwordInput).toHaveAttribute('type', 'text');

      await user.click(screen.getAllByRole('button', { name: /Masquer le mot de passe/i })[0]);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });
  }

  private testPasswordStrengthBar() {
    it('affiche la barre de force du mot de passe lors de la saisie', async () => {
      const { user } = this.renderPage();
      const passwordInput = screen.getByLabelText('Mot de passe');
      await user.type(passwordInput, 'StrongP@ss1!');

      await waitFor(() => {
        expect(screen.getByText(/Force/)).toBeInTheDocument();
      });
    });
  }

  private testPasswordPlaceholders() {
    it('affiche des placeholders décrivant les règles du mot de passe', () => {
      this.renderPage();
      expect(screen.getByPlaceholderText(/8\+ car\./i)).toBeInTheDocument();
    });
  }

  private testKeePassTip() {
    it('affiche le conseil KeePass', () => {
      this.renderPage();
      expect(screen.getByText(/KeePass/)).toBeInTheDocument();
    });
  }
}

new RegisterPageIntTest().run();
