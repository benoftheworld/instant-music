import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { BaseIntegrationTest } from '../base/BaseIntegrationTest';
import { seedDB, getDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import { createTestQueryClient } from '@/tests/shared/renderHelpers';
import LoginPage from '@/pages/auth/LoginPage';

class AuthFlowIntTest extends BaseIntegrationTest {
  run() {
    describe('Auth Flow (intégration)', () => {
      this.setupServer();

      beforeEach(() => {
        seedDB(createSeededDB());
      });

      this.testLoginSuccessful();
      this.testLoginFailed();
      this.testTokenInDB();
    });
  }

  private renderApp(initialEntries: string[] = ['/login']) {
    const queryClient = createTestQueryClient();
    const user = userEvent.setup();
    const result = render(
      React.createElement(
        QueryClientProvider,
        { client: queryClient },
        React.createElement(
          MemoryRouter,
          { initialEntries, future: { v7_relativeSplatPath: true } },
          React.createElement(
            Routes,
            null,
            React.createElement(Route, { path: '/login', element: React.createElement(LoginPage) }),
            React.createElement(Route, { path: '/', element: React.createElement('div', null, 'Home Page') }),
          ),
        ),
      ),
    );
    return { ...result, user };
  }

  private testLoginSuccessful() {
    it('login → l\'utilisateur est enregistré dans la DB', async () => {
      const { user } = this.renderApp();

      const usernameField = screen.getByLabelText(/Identifiant/);
      const passwordField = screen.getByLabelText(/Mot de passe/);
      await user.clear(usernameField);
      await user.type(usernameField, 'alice');
      await user.clear(passwordField);
      await user.type(passwordField, 'password123');
      await user.click(screen.getByRole('button', { name: /Se connecter/ }));

      await waitFor(() => {
        const db = getDB();
        expect(db.currentUser).not.toBeNull();
        expect(db.currentUser!.username).toBe('alice');
      });
    });
  }

  private testLoginFailed() {
    it('login échoue avec un mauvais utilisateur', async () => {
      const { user } = this.renderApp();

      const usernameField = screen.getByLabelText(/Identifiant/);
      const passwordField = screen.getByLabelText(/Mot de passe/);
      await user.clear(usernameField);
      await user.type(usernameField, 'nonexistent');
      await user.clear(passwordField);
      await user.type(passwordField, 'wrong');
      await user.click(screen.getByRole('button', { name: /Se connecter/ }));

      await waitFor(() => {
        expect(screen.getByText(/Identifiants invalides/)).toBeInTheDocument();
      });
    });
  }

  private testTokenInDB() {
    it('après login, le token est dans la DB MSW', async () => {
      const { user } = this.renderApp();

      const usernameField = screen.getByLabelText(/Identifiant/);
      const passwordField = screen.getByLabelText(/Mot de passe/);
      await user.clear(usernameField);
      await user.type(usernameField, 'alice');
      await user.clear(passwordField);
      await user.type(passwordField, 'password123');
      await user.click(screen.getByRole('button', { name: /Se connecter/ }));

      await waitFor(() => {
        const db = getDB();
        expect(db.accessToken).toBeTruthy();
      });
    });
  }
}

new AuthFlowIntTest().run();
