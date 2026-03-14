/**
 * Classe abstraite de base pour les tests de hooks React.
 *
 * Factorise : renderHook avec wrapper providers, cleanup.
 */
import React, { type ReactNode } from 'react';
import { renderHook, type RenderHookResult } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { beforeEach, vi } from 'vitest';
import { createTestQueryClient, resetStores } from '@/tests/shared/renderHelpers';

export abstract class BaseHookTest {
  protected abstract name: string;
  protected queryClient!: QueryClient;

  protected setup() {
    beforeEach(() => {
      vi.clearAllMocks();
      resetStores();
      this.queryClient = createTestQueryClient();
    });
  }

  /**
   * Crée un wrapper avec les providers nécessaires.
   * @param initialEntries Entrées du MemoryRouter
   */
  protected createWrapper(initialEntries: string[] = ['/']) {
    const qc = this.queryClient;
    return function Wrapper({ children }: { children: ReactNode }) {
      return React.createElement(
        QueryClientProvider,
        { client: qc },
        React.createElement(
          MemoryRouter,
          { initialEntries },
          children,
        ),
      );
    };
  }

  /** Render un hook avec les providers par défaut */
  protected renderTestHook<TResult>(
    hook: () => TResult,
    initialEntries?: string[],
  ): RenderHookResult<TResult, unknown> {
    return renderHook(hook, {
      wrapper: this.createWrapper(initialEntries),
    });
  }
}
