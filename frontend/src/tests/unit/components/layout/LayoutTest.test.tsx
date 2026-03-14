import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('@/hooks/useSiteStatus', () => ({
  useSiteStatus: vi.fn(() => ({
    maintenance: false,
    maintenance_title: '',
    maintenance_message: '',
    banner: null,
  })),
}));

vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn((selector?: any) => {
    const state = { user: null, isAuthenticated: false, updateUser: vi.fn(), login: vi.fn(), logout: vi.fn() };
    return selector ? selector(state) : state;
  }),
}));

vi.mock('@/components/layout/Navbar', () => ({ default: () => <nav data-testid="navbar">Navbar</nav> }));
vi.mock('@/components/layout/SiteBanner', () => ({ default: () => null }));
vi.mock('@/components/layout/ConsentBanner', () => ({ default: () => null }));
vi.mock('@/components/layout/MaintenancePage', () => ({
  default: ({ title }: { title: string }) => <div data-testid="maintenance">{title}</div>,
}));

import Layout from '@/components/layout/Layout';
import { useSiteStatus } from '@/hooks/useSiteStatus';
import { useAuthStore } from '@/store/authStore';

class LayoutTest {
  run() {
    describe('Layout', () => {
      this.testRendersNavbarAndFooter();
      this.testMaintenanceMode();
      this.testStaffSeesMaintWarning();
    });
  }

  private testRendersNavbarAndFooter() {
    it('affiche la navbar et le footer', () => {
      render(
        <MemoryRouter>
          <Layout />
        </MemoryRouter>,
      );
      expect(screen.getByText(/InstantMusic/)).toBeInTheDocument();
      expect(screen.getByText(/Politique de confidentialité/)).toBeInTheDocument();
    });
  }

  private testMaintenanceMode() {
    it('affiche la page de maintenance pour les non-staff', () => {
      vi.mocked(useSiteStatus).mockReturnValue({
        maintenance: true,
        maintenance_title: 'En maintenance',
        maintenance_message: 'Revenez bientôt',
        banner: null,
      } as any);
      vi.mocked(useAuthStore).mockImplementation((selector?: any) => {
        const state = { user: null, isAuthenticated: false, updateUser: vi.fn(), login: vi.fn(), logout: vi.fn() };
        return selector ? selector(state) : state;
      });
      render(
        <MemoryRouter>
          <Layout />
        </MemoryRouter>,
      );
      expect(screen.getByTestId('maintenance')).toBeInTheDocument();
    });
  }

  private testStaffSeesMaintWarning() {
    it("affiche l'avertissement maintenance pour les staff", () => {
      vi.mocked(useSiteStatus).mockReturnValue({
        maintenance: true,
        maintenance_title: 'En maintenance',
        maintenance_message: '',
        banner: null,
      } as any);
      vi.mocked(useAuthStore).mockImplementation((selector?: any) => {
        const state = { user: { is_staff: true }, isAuthenticated: true, updateUser: vi.fn(), login: vi.fn(), logout: vi.fn() };
        return selector ? selector(state) : state;
      });
      render(
        <MemoryRouter>
          <Layout />
        </MemoryRouter>,
      );
      expect(screen.getByText(/Mode maintenance actif/)).toBeInTheDocument();
    });
  }
}

new LayoutTest().run();
