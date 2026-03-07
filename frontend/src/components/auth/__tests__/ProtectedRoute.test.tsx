import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

function renderWithRouter(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<div>Dashboard</div>} />
        </Route>
      </Routes>
    </MemoryRouter>
  );
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({
      user: null,
      tokens: null,
      isAuthenticated: false,
    });
  });

  it('redirige vers /login si non authentifie', () => {
    renderWithRouter('/dashboard');
    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  it('affiche le contenu protege si authentifie', () => {
    useAuthStore.setState({
      user: { id: '1', username: 'test' } as any,
      tokens: { access: 'a', refresh: 'r' },
      isAuthenticated: true,
    });
    renderWithRouter('/dashboard');
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });
});
