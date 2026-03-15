/**
 * Helpers de rendu pour les tests React.
 * Wraps les composants avec les providers nécessaires (Router, QueryClient, stores).
 */
import React, { type ReactElement } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { MemoryRouter, type MemoryRouterProps } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '@/store/authStore';
import { useNotificationStore } from '@/store/notificationStore';
import type { User } from '@/types';

/** Crée un QueryClient configuré pour les tests (pas de retry, pas de cache). */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

interface RenderWithProvidersOptions extends Omit<RenderOptions, 'wrapper'> {
  /** Entrées initiales du MemoryRouter */
  initialEntries?: MemoryRouterProps['initialEntries'];
  /** État initial du authStore */
  authState?: { user?: User | null; isAuthenticated?: boolean };
  /** QueryClient custom (sinon un nouveau sera créé) */
  queryClient?: QueryClient;
}

/**
 * Render un composant avec tous les providers nécessaires :
 * QueryClientProvider, MemoryRouter, et état initial des stores.
 */
export function renderWithProviders(
  ui: ReactElement,
  options: RenderWithProvidersOptions = {},
) {
  const {
    initialEntries = ['/'],
    authState,
    queryClient = createTestQueryClient(),
    ...renderOptions
  } = options;

  // Reset des stores avant chaque rendu
  if (authState) {
    useAuthStore.setState({
      user: authState.user ?? null,
      isAuthenticated: authState.isAuthenticated ?? false,
    });
  }

  function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      React.createElement(
        MemoryRouter,
        { initialEntries, future: { v7_relativeSplatPath: true } },
        children,
      ),
    );
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    queryClient,
  };
}

/**
 * Render avec MemoryRouter uniquement (pas de QueryClient).
 */
export function renderWithRouter(
  ui: ReactElement,
  initialEntries: MemoryRouterProps['initialEntries'] = ['/'],
  options?: Omit<RenderOptions, 'wrapper'>,
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      MemoryRouter,
      { initialEntries, future: { v7_relativeSplatPath: true } },
      children,
    );
  }

  return render(ui, { wrapper: Wrapper, ...options });
}

/**
 * Reset tous les stores Zustand à leur état initial.
 */
export function resetStores() {
  if (typeof useAuthStore.setState === 'function') {
    useAuthStore.setState({ user: null, isAuthenticated: false });
  }
  if (typeof useNotificationStore.setState === 'function') {
    useNotificationStore.setState({
      invitations: [],
      friendRequests: [],
      socialNotifications: [],
    });
  }
}
