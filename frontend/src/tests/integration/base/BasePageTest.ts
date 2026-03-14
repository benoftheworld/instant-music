/**
 * Classe abstraite pour les tests d'intégration de pages.
 *
 * Étend BaseIntegrationTest avec render helpers spécifiques aux pages.
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BaseIntegrationTest } from './BaseIntegrationTest';
import { createTestQueryClient } from '@/tests/shared/renderHelpers';

export abstract class BasePageTest extends BaseIntegrationTest {
  protected abstract getRoute(): string;
  protected abstract getComponent(): React.ComponentType;

  protected renderPage(initialEntries?: string[]) {
    const queryClient = createTestQueryClient();
    const Component = this.getComponent();
    const route = this.getRoute();
    const entries = initialEntries ?? [route];

    const user = userEvent.setup();
    const result = render(
      React.createElement(
        QueryClientProvider,
        { client: queryClient },
        React.createElement(
          MemoryRouter,
          { initialEntries: entries },
          React.createElement(
            Routes,
            null,
            React.createElement(Route, { path: route, element: React.createElement(Component) }),
          ),
        ),
      ),
    );

    return { ...result, user, queryClient };
  }

  protected async waitForLoad() {
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    }, { timeout: 3000 });
  }
}
