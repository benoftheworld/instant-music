/**
 * Classe abstraite de base pour les tests de stores Zustand.
 *
 * Factorise : reset de l'état, helpers pour accéder au store.
 */
import { beforeEach } from 'vitest';

type StoreApi<T> = {
  getState: () => T;
  setState: (partial: Partial<T>) => void;
};

export abstract class BaseStoreTest<TState extends object> {
  protected abstract name: string;

  /** Retourne le store Zustand sous test */
  protected abstract getStore(): StoreApi<TState>;

  /** Retourne l'état initial attendu */
  protected abstract getInitialState(): Partial<TState>;

  /** Configure le reset du store avant chaque test */
  protected setup() {
    beforeEach(() => {
      this.getStore().setState(this.getInitialState() as TState);
    });
  }

  /** Raccourci pour getState() */
  protected state(): TState {
    return this.getStore().getState();
  }

  /** Raccourci pour setState() */
  protected setState(partial: Partial<TState>) {
    this.getStore().setState(partial);
  }
}
