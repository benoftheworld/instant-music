import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import GuestRoute from '@/components/auth/GuestRoute';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { createUser } from '@/tests/shared/factories';

vi.mock('@/services/tokenService', () => ({
  tokenService: { setAccessToken: vi.fn(), clearTokens: vi.fn(), getAccessToken: vi.fn(), isTokenExpired: vi.fn() },
}));

class AuthRoutesTest {
  run() {
    describe('GuestRoute', () => {
      beforeEach(() => useAuthStore.setState({ user: null, isAuthenticated: false }));
      this.testGuestAllowed();
      this.testGuestRedirects();
    });

    describe('ProtectedRoute', () => {
      beforeEach(() => useAuthStore.setState({ user: null, isAuthenticated: false }));
      this.testProtectedRedirects();
      this.testProtectedAllowed();
    });
  }

  private testGuestAllowed() {
    it('non authentifié — affiche l\'outlet', () => {
      render(
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route element={<GuestRoute />}>
              <Route path="/login" element={<div>Login Page</div>} />
            </Route>
            <Route path="/" element={<div>Home</div>} />
          </Routes>
        </MemoryRouter>,
      );
      expect(screen.getByText('Login Page')).toBeInTheDocument();
    });
  }

  private testGuestRedirects() {
    it('authentifié — redirige vers /', () => {
      useAuthStore.setState({ user: createUser(), isAuthenticated: true });
      render(
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route element={<GuestRoute />}>
              <Route path="/login" element={<div>Login Page</div>} />
            </Route>
            <Route path="/" element={<div>Home</div>} />
          </Routes>
        </MemoryRouter>,
      );
      expect(screen.getByText('Home')).toBeInTheDocument();
    });
  }

  private testProtectedRedirects() {
    it('non authentifié — redirige vers /login', () => {
      render(
        <MemoryRouter initialEntries={['/profile']}>
          <Routes>
            <Route element={<ProtectedRoute />}>
              <Route path="/profile" element={<div>Profile</div>} />
            </Route>
            <Route path="/login" element={<div>Login</div>} />
          </Routes>
        </MemoryRouter>,
      );
      expect(screen.getByText('Login')).toBeInTheDocument();
    });
  }

  private testProtectedAllowed() {
    it('authentifié — affiche l\'outlet', () => {
      useAuthStore.setState({ user: createUser(), isAuthenticated: true });
      render(
        <MemoryRouter initialEntries={['/profile']}>
          <Routes>
            <Route element={<ProtectedRoute />}>
              <Route path="/profile" element={<div>Profile</div>} />
            </Route>
            <Route path="/login" element={<div>Login</div>} />
          </Routes>
        </MemoryRouter>,
      );
      expect(screen.getByText('Profile')).toBeInTheDocument();
    });
  }
}

new AuthRoutesTest().run();
