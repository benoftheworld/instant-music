import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BaseServiceTest } from '../base/BaseServiceTest';

vi.mock('@/services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import { adminService } from '@/services/adminService';
import { api } from '@/services/api';

class AdminServiceTest extends BaseServiceTest {
  protected name = 'adminService';

  run() {
    describe('adminService', () => {
      this.setup(api);

      this.testGetStatus();
      this.testGetStatusMaintenance();
      this.testGetLegalPage();
      this.testGetLegalPageNotFound();
    });
  }

  private testGetStatus() {
    it('getStatus — normal', async () => {
      const status = { maintenance: false, maintenance_title: '', maintenance_message: '', banner: { enabled: false, message: '', color: 'info', dismissible: true } };
      this.mockGet('/administration/status/', status);
      const result = await adminService.getStatus();
      expect(result.maintenance).toBe(false);
    });
  }

  private testGetStatusMaintenance() {
    it('getStatus — maintenance activée', async () => {
      const status = { maintenance: true, maintenance_title: 'Maintenance', maintenance_message: 'En cours', banner: { enabled: true, message: 'Maintenance', color: 'warning', dismissible: false } };
      this.mockGet('/administration/status/', status);
      const result = await adminService.getStatus();
      expect(result.maintenance).toBe(true);
      expect(result.banner.enabled).toBe(true);
    });
  }

  private testGetLegalPage() {
    it('getLegalPage — succès', async () => {
      const page = { title: 'Mentions légales', content: '<p>Test</p>', updated_at: '2024-01-01' };
      this.mockGet('/administration/legal/legal/', page);
      const result = await adminService.getLegalPage('legal');
      expect(result.title).toBe('Mentions légales');
    });
  }

  private testGetLegalPageNotFound() {
    it('getLegalPage — erreur 404', async () => {
      this.mockError('get', 404, { detail: 'Page introuvable.' });
      await expect(adminService.getLegalPage('legal')).rejects.toThrow();
    });
  }
}

new AdminServiceTest().run();
