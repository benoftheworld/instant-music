import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BaseServiceTest } from '../base/BaseServiceTest';

vi.mock('@/services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import { userService } from '@/services/userService';
import { api } from '@/services/api';

class UserServiceTest extends BaseServiceTest {
  protected name = 'userService';

  run() {
    describe('userService', () => {
      this.setup(api);

      this.testUsernameExists();
      this.testUsernameNotExists();
      this.testEmailExists();
      this.testEmailNotExists();
      this.testRecordCookieConsent();
      this.testUsernameExistsError();
    });
  }

  private testUsernameExists() {
    it('usernameExists — retourne true', async () => {
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { exists: true } });
      const result = await userService.usernameExists('alice');
      expect(result).toBe(true);
      expect(api.get).toHaveBeenCalledWith('/users/exists/', { params: { username: 'alice' } });
    });
  }

  private testUsernameNotExists() {
    it('usernameExists — retourne false', async () => {
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { exists: false } });
      const result = await userService.usernameExists('nobody');
      expect(result).toBe(false);
    });
  }

  private testEmailExists() {
    it('emailExists — retourne true', async () => {
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { exists: true } });
      const result = await userService.emailExists('test@test.com');
      expect(result).toBe(true);
      expect(api.get).toHaveBeenCalledWith('/users/exists/', { params: { email: 'test@test.com' } });
    });
  }

  private testEmailNotExists() {
    it('emailExists — retourne false', async () => {
      (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
      const result = await userService.emailExists('nope@test.com');
      expect(result).toBe(false);
    });
  }

  private testRecordCookieConsent() {
    it('recordCookieConsent — succès', async () => {
      (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
      await userService.recordCookieConsent();
      expect(api.post).toHaveBeenCalledWith('/users/cookie_consent/');
    });
  }

  private testUsernameExistsError() {
    it('usernameExists — erreur réseau', async () => {
      this.mockError('get', 500, { detail: 'Erreur serveur' });
      await expect(userService.usernameExists('alice')).rejects.toThrow();
    });
  }
}

new UserServiceTest().run();
