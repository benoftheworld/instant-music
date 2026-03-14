import { describe } from 'vitest';
import { BaseUtilTest } from '../base/BaseUtilTest';
import { getApiErrorMessage } from '@/utils/apiError';
import axios, { AxiosError, AxiosHeaders } from 'axios';

class ApiErrorTest extends BaseUtilTest {
  protected name = 'getApiErrorMessage';

  run() {
    describe('getApiErrorMessage', () => {
      this.testAxiosStringData();
      this.testAxiosErrorField();
      this.testAxiosDetailField();
      this.testAxiosMessageField();
      this.testAxiosValidationArray();
      this.testStandardError();
      this.testFallback();
      this.testCustomFallback();
      this.testNonAxiosNonError();
    });
  }

  private testAxiosStringData() {
    const err = new AxiosError('fail', '400', undefined, undefined, {
      data: 'Erreur texte brut',
      status: 400,
      statusText: 'Bad Request',
      headers: {},
      config: { headers: new AxiosHeaders() },
    });

    this.testPureFunction(
      'extrait une string directe de response.data',
      () => getApiErrorMessage(err),
      [{ input: undefined as any, expected: 'Erreur texte brut', label: 'string data' }],
    );
  }

  private testAxiosErrorField() {
    const err = new AxiosError('fail', '400', undefined, undefined, {
      data: { error: 'Champ error' },
      status: 400,
      statusText: 'Bad Request',
      headers: {},
      config: { headers: new AxiosHeaders() },
    });

    this.testPureFunction(
      'extrait data.error',
      () => getApiErrorMessage(err),
      [{ input: undefined as any, expected: 'Champ error', label: 'data.error' }],
    );
  }

  private testAxiosDetailField() {
    const err = new AxiosError('fail', '401', undefined, undefined, {
      data: { detail: 'Non authentifié.' },
      status: 401,
      statusText: 'Unauthorized',
      headers: {},
      config: { headers: new AxiosHeaders() },
    });

    this.testPureFunction(
      'extrait data.detail',
      () => getApiErrorMessage(err),
      [{ input: undefined as any, expected: 'Non authentifié.', label: 'data.detail' }],
    );
  }

  private testAxiosMessageField() {
    const err = new AxiosError('fail', '403', undefined, undefined, {
      data: { message: 'Accès refusé.' },
      status: 403,
      statusText: 'Forbidden',
      headers: {},
      config: { headers: new AxiosHeaders() },
    });

    this.testPureFunction(
      'extrait data.message',
      () => getApiErrorMessage(err),
      [{ input: undefined as any, expected: 'Accès refusé.', label: 'data.message' }],
    );
  }

  private testAxiosValidationArray() {
    const err = new AxiosError('fail', '400', undefined, undefined, {
      data: { username: ['Ce nom est déjà pris.', 'Trop court.'] },
      status: 400,
      statusText: 'Bad Request',
      headers: {},
      config: { headers: new AxiosHeaders() },
    });

    this.testPureFunction(
      'extrait le premier message de validation DRF',
      () => getApiErrorMessage(err),
      [{ input: undefined as any, expected: 'Ce nom est déjà pris.', label: 'DRF validation' }],
    );
  }

  private testStandardError() {
    this.testPureFunction(
      'extrait message d\'une Error standard',
      () => getApiErrorMessage(new Error('custom error')),
      [{ input: undefined as any, expected: 'custom error', label: 'Error.message' }],
    );
  }

  private testFallback() {
    this.testPureFunction(
      'retourne le fallback par défaut pour une valeur inconnue',
      () => getApiErrorMessage(42),
      [{ input: undefined as any, expected: 'Une erreur est survenue.', label: 'default fallback' }],
    );
  }

  private testCustomFallback() {
    this.testPureFunction(
      'retourne un fallback personnalisé',
      () => getApiErrorMessage(null, 'Oops custom'),
      [{ input: undefined as any, expected: 'Oops custom', label: 'custom fallback' }],
    );
  }

  private testNonAxiosNonError() {
    this.testPureFunction(
      'retourne le fallback pour undefined',
      () => getApiErrorMessage(undefined),
      [{ input: undefined as any, expected: 'Une erreur est survenue.', label: 'undefined input' }],
    );
  }
}

new ApiErrorTest().run();
