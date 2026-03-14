import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BaseServiceTest } from '../base/BaseServiceTest';

// Mock le module api
vi.mock('@/services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  refreshAccessToken: vi.fn(),
  getMediaUrl: vi.fn((p: string) => p ? `http://localhost:8000${p}` : undefined),
}));

import { authService } from '@/services/authService';
import { api } from '@/services/api';
import { createUser, createAuthResponse, createLoginCredentials, createRegisterData } from '@/tests/shared/factories';

class AuthServiceTest extends BaseServiceTest {
  protected name = 'authService';

  run() {
    describe('authService', () => {
      this.setup(api);

      this.testLogin();
      this.testLoginError();
      this.testRegister();
      this.testRegisterError();
      this.testGetCurrentUser();
      this.testUpdateProfile();
      this.testChangePassword();
      this.testRequestPasswordReset();
      this.testConfirmPasswordReset();
      this.testLogout();
      this.testLogoutNetworkError();
    });
  }

  private testLogin() {
    it('login — succès', async () => {
      const credentials = createLoginCredentials();
      const authResp = createAuthResponse();
      this.mockPost('/auth/login/', authResp);

      const result = await authService.login(credentials);

      expect(result).toEqual(authResp);
      this.expectCall('post', '/auth/login/', credentials);
    });
  }

  private testLoginError() {
    it('login — erreur 401', async () => {
      this.mockError('post', 401, { detail: 'Identifiants invalides.' });
      await expect(authService.login(createLoginCredentials())).rejects.toThrow();
    });
  }

  private testRegister() {
    it('register — succès', async () => {
      const data = createRegisterData();
      const authResp = createAuthResponse();
      this.mockPost('/auth/register/', authResp);

      const result = await authService.register(data);

      expect(result).toEqual(authResp);
      this.expectCall('post', '/auth/register/', data);
    });
  }

  private testRegisterError() {
    it('register — erreur 400 (username pris)', async () => {
      this.mockError('post', 400, { username: ['Ce nom est déjà pris.'] });
      await expect(authService.register(createRegisterData())).rejects.toThrow();
    });
  }

  private testGetCurrentUser() {
    it('getCurrentUser — succès', async () => {
      const user = createUser();
      this.mockGet('/users/me/', user);

      const result = await authService.getCurrentUser();

      expect(result).toEqual(user);
      this.expectCall('get', '/users/me/');
    });
  }

  private testUpdateProfile() {
    it('updateProfile — succès', async () => {
      const user = createUser({ username: 'updated' });
      this.mockPatch('/users/me/', user);

      const result = await authService.updateProfile({ username: 'updated' });

      expect(result).toEqual(user);
    });
  }

  private testChangePassword() {
    it('changePassword — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });

      await authService.changePassword('old123', 'new456');

      expect(api.post).toHaveBeenCalledWith('/users/change_password/', {
        old_password: 'old123',
        new_password: 'new456',
      });
    });
  }

  private testRequestPasswordReset() {
    it('requestPasswordReset — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });

      await authService.requestPasswordReset('test@example.com');

      expect(api.post).toHaveBeenCalledWith('/auth/password/reset/', { email: 'test@example.com' });
    });
  }

  private testConfirmPasswordReset() {
    it('confirmPasswordReset — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });

      await authService.confirmPasswordReset('uid1', 'token1', 'newpass');

      expect(api.post).toHaveBeenCalledWith('/auth/password/reset/confirm/', {
        uid: 'uid1',
        token: 'token1',
        new_password: 'newpass',
        new_password2: 'newpass',
      });
    });
  }

  private testLogout() {
    it('logout — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });

      await authService.logout();

      expect(api.post).toHaveBeenCalledWith('/auth/logout/');
    });
  }

  private testLogoutNetworkError() {
    it('logout — ignore les erreurs réseau', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Network Error'));

      // Ne devrait pas throw
      await authService.logout();
    });
  }
}

new AuthServiceTest().run();
