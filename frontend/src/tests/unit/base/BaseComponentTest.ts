/**
 * Classe abstraite de base pour les tests de composants React.
 *
 * Factorise : rendu avec providers, helpers pour interactions et assertions.
 */
import type { ReactElement } from 'react';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, vi } from 'vitest';
import { renderWithProviders, resetStores } from '@/tests/shared/renderHelpers';
import type { User } from '@/types';

interface RenderOptions {
  initialEntries?: string[];
  authState?: { user?: User | null; isAuthenticated?: boolean };
}

export abstract class BaseComponentTest {
  protected abstract name: string;

  /** Retourne le composant sous test avec ses props par défaut */
  protected abstract renderSubject(propsOverrides?: Record<string, unknown>): ReactElement;

  protected setup() {
    beforeEach(() => {
      vi.clearAllMocks();
      resetStores();
    });
  }

  /** Rend le composant avec les providers et retourne les utilitaires */
  protected renderComponent(propsOverrides?: Record<string, unknown>, options?: RenderOptions) {
    const user = userEvent.setup();
    const result = renderWithProviders(this.renderSubject(propsOverrides), {
      initialEntries: options?.initialEntries,
      authState: options?.authState,
    });
    return { ...result, user };
  }

  /** Vérifie qu'un texte est rendu dans le DOM */
  protected expectText(text: string | RegExp) {
    expect(screen.getByText(text)).toBeInTheDocument();
  }

  /** Vérifie qu'un texte n'est PAS rendu dans le DOM */
  protected expectNoText(text: string | RegExp) {
    expect(screen.queryByText(text)).not.toBeInTheDocument();
  }

  /** Vérifie qu'un rôle est présent */
  protected expectRole(role: string, name?: string | RegExp) {
    if (name) {
      expect(screen.getByRole(role, { name })).toBeInTheDocument();
    } else {
      expect(screen.getByRole(role)).toBeInTheDocument();
    }
  }

  /** Vérifie qu'un test-id est présent */
  protected expectTestId(testId: string) {
    expect(screen.getByTestId(testId)).toBeInTheDocument();
  }
}
