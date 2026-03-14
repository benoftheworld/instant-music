/**
 * Classe abstraite de base pour les tests de services API.
 *
 * Factorise : mock d'axios, helpers pour simuler succès/erreur,
 * assertions sur les appels API.
 */
import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';

/** Type utilitaire pour un module axios mocké */
interface MockedApi {
  get: Mock;
  post: Mock;
  put: Mock;
  patch: Mock;
  delete: Mock;
}

export abstract class BaseServiceTest {
  /** Nom du describe principal */
  protected abstract name: string;

  /** Retourne le module api mocké */
  protected api!: MockedApi;

  /** Configure les mocks avant chaque test. Passer `api` pour l'assigner automatiquement. */
  protected setup(apiRef?: any) {
    if (apiRef) {
      this.api = apiRef as unknown as MockedApi;
    }
    beforeEach(() => {
      vi.clearAllMocks();
    });
  }

  /** Mock une réponse GET réussie. L'URL optionnelle est ignorée (pour lisibilité). */
  protected mockGet(...args: unknown[]) {
    const response = args.length > 1 ? args[args.length - 1] : args[0];
    this.api.get.mockResolvedValueOnce({ data: response });
  }

  /** Mock une réponse POST réussie */
  protected mockPost(...args: unknown[]) {
    const response = args.length > 1 ? args[args.length - 1] : args[0];
    this.api.post.mockResolvedValueOnce({ data: response });
  }

  /** Mock une réponse PATCH réussie */
  protected mockPatch(...args: unknown[]) {
    const response = args.length > 1 ? args[args.length - 1] : args[0];
    this.api.patch.mockResolvedValueOnce({ data: response });
  }

  /** Mock une réponse PUT réussie */
  protected mockPut(...args: unknown[]) {
    const response = args.length > 1 ? args[args.length - 1] : args[0];
    this.api.put.mockResolvedValueOnce({ data: response });
  }

  /** Mock une réponse DELETE réussie */
  protected mockDelete(...args: unknown[]) {
    const response = args.length > 1 ? args[args.length - 1] : args[0];
    this.api.delete.mockResolvedValueOnce({ data: response });
  }

  /** Mock une erreur Axios pour une méthode donnée */
  protected mockError(
    method: 'get' | 'post' | 'put' | 'patch' | 'delete',
    status: number,
    data?: unknown,
  ) {
    const error = {
      isAxiosError: true,
      response: { status, data: data ?? { detail: `Error ${status}` } },
      message: `Request failed with status code ${status}`,
    };
    this.api[method].mockRejectedValueOnce(error);
  }

  /** Vérifie qu'un appel API a été fait avec les bons paramètres */
  protected expectCall(
    method: 'get' | 'post' | 'put' | 'patch' | 'delete',
    url: string,
    ...args: unknown[]
  ) {
    expect(this.api[method]).toHaveBeenCalledWith(url, ...args);
  }

  /** Vérifie qu'un appel API a été fait (sans vérifier les params) */
  protected expectCalled(method: 'get' | 'post' | 'put' | 'patch' | 'delete') {
    expect(this.api[method]).toHaveBeenCalled();
  }
}
