import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

vi.mock('@/services/tokenService', () => ({
  tokenService: { setAccessToken: vi.fn(), clearTokens: vi.fn(), getAccessToken: vi.fn(), isTokenExpired: vi.fn() },
}));

vi.mock('@/services/userService', () => ({
  userService: { recordCookieConsent: vi.fn().mockResolvedValue(undefined) },
}));

import ConsentBanner from '@/components/layout/ConsentBanner';

class ConsentBannerTest {
  run() {
    describe('ConsentBanner', () => {
      beforeEach(() => {
        localStorage.clear();
        useAuthStore.setState({ user: null, isAuthenticated: false });
      });

      this.testShowsBanner();
      this.testAcceptHidesBanner();
      this.testHiddenAfterConsent();
    });
  }

  private testShowsBanner() {
    it('affiche la bannière si pas de consentement', () => {
      render(<ConsentBanner />, { wrapper: MemoryRouter });
      expect(screen.getByText(/politique de confidentialité/i)).toBeInTheDocument();
    });
  }

  private testAcceptHidesBanner() {
    it('accepter masque la bannière', async () => {
      render(<ConsentBanner />, { wrapper: MemoryRouter });
      await userEvent.click(screen.getByText("J'accepte"));
      expect(screen.queryByText(/politique de confidentialité/i)).not.toBeInTheDocument();
    });
  }

  private testHiddenAfterConsent() {
    it('ne montre pas la bannière si consentement déjà donné', () => {
      localStorage.setItem('rgpd_consent', JSON.stringify('2024-01-01'));
      render(<ConsentBanner />, { wrapper: MemoryRouter });
      expect(screen.queryByText(/politique de confidentialité/i)).not.toBeInTheDocument();
    });
  }
}

new ConsentBannerTest().run();
