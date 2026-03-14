import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

vi.mock('@/services/adminService', () => ({
  adminService: {
    getStatus: vi.fn().mockResolvedValue({
      maintenance: false,
      maintenance_title: '',
      maintenance_message: '',
      banner: { enabled: false, message: '', color: 'info', dismissible: true },
    }),
  },
}));

import { useSiteStatus } from '@/hooks/useSiteStatus';

class UseSiteStatusTest {
  private createWrapper() {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    return ({ children }: { children: React.ReactNode }) =>
      React.createElement(QueryClientProvider, { client: qc }, children);
  }

  run() {
    describe('useSiteStatus', () => {
      this.testReturnsFallback();
      this.testReturnsSiteStatus();
    });
  }

  private testReturnsFallback() {
    it('retourne le fallback par défaut avant le chargement', () => {
      const { result } = renderHook(() => useSiteStatus(), { wrapper: this.createWrapper() });
      expect(result.current.maintenance).toBe(false);
      expect(result.current.banner.enabled).toBe(false);
    });
  }

  private testReturnsSiteStatus() {
    it('retourne les données du service après chargement', async () => {
      const { adminService } = await import('@/services/adminService');
      (adminService.getStatus as ReturnType<typeof vi.fn>).mockResolvedValue({
        maintenance: true,
        maintenance_title: 'En pause',
        maintenance_message: 'Retour bientôt',
        banner: { enabled: true, message: 'Hello', color: 'warning', dismissible: false },
      });

      const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(QueryClientProvider, { client: qc }, children);

      const { result } = renderHook(() => useSiteStatus(), { wrapper });

      // Wait for query to resolve
      await vi.waitFor(() => {
        expect(result.current.maintenance).toBe(true);
      });
      expect(result.current.maintenance_title).toBe('En pause');
    });
  }
}

new UseSiteStatusTest().run();
