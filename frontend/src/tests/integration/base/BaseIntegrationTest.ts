/**
 * Classe abstraite de base pour les tests d'intégration.
 *
 * Gère le cycle de vie du serveur MSW et du mock DB.
 */
import { beforeAll, afterAll, afterEach, type TestAPI } from 'vitest';
import { server } from '../msw/server';
import { resetDB, seedDB, getDB, type MockDB } from '../msw/db';
import { createSeededDB } from '../msw/fixtures';
import { resetStores } from '@/tests/shared/renderHelpers';
import type { HttpHandler } from 'msw';

export abstract class BaseIntegrationTest {
  protected setupServer() {
    beforeAll(() => {
      server.listen({ onUnhandledRequest: 'warn' });
    });

    afterEach(() => {
      server.resetHandlers();
      resetDB();
      resetStores();
      localStorage.clear();
    });

    afterAll(() => {
      server.close();
    });
  }

  /** Peuple la DB avec les fixtures par défaut */
  protected seedDefaults(): void {
    seedDB(createSeededDB());
  }

  /** Accès direct au mock DB */
  protected getDb(): MockDB {
    return getDB();
  }

  /** Surcharge un handler MSW pour un test spécifique */
  protected overrideHandler(...handlers: HttpHandler[]): void {
    server.use(...handlers);
  }
}
