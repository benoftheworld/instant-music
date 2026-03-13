import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { useLogout } from '@/hooks/useAuth';
import { authService } from '@/services/authService';
import NotificationBell from './NotificationBell';
import DesktopNav from './navbar/DesktopNav';
import MobileNav from './navbar/MobileNav';

export default function Navbar() {
  const { isAuthenticated, user, updateUser } = useAuthStore();
  const logout = useLogout();
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isAdminOpen, setIsAdminOpen] = useState(false);
  const [prevPathname, setPrevPathname] = useState(location.pathname);

  // Ferme le menu mobile à chaque changement de route
  if (prevPathname !== location.pathname) {
    setPrevPathname(location.pathname);
    setIsMenuOpen(false);
    setIsAdminOpen(false);
  }

  useEffect(() => {
    if (!isAuthenticated) return;
    authService.getCurrentUser().then(updateUser).catch((err) => console.error('Failed to fetch current user:', err));
  }, [isAuthenticated]);

  const closeMenu = () => setIsMenuOpen(false);

  return (
    <nav className="bg-dark text-cream-100 shadow-lg border-b-4 border-primary-500">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">

          {/* ── Logo ── */}
          <Link to="/" className="text-2xl font-bold hover:text-primary-400 transition-colors flex items-center shrink-0">
            <span className="text-primary-600">Instant</span>Music
          </Link>

          <DesktopNav
            isAuthenticated={isAuthenticated}
            user={user}
            onLogout={logout}
          />

          {/* ── Bouton hamburger (mobile uniquement) ── */}
          <div className="md:hidden flex items-center gap-2">
            {isAuthenticated && <NotificationBell />}
            <button
              className="flex items-center justify-center w-10 h-10 rounded-md hover:bg-dark-600 transition-colors"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              aria-label={isMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
              aria-expanded={isMenuOpen}
              aria-controls="mobile-menu"
            >
              {isMenuOpen ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {isMenuOpen && (
        <MobileNav
          isAuthenticated={isAuthenticated}
          user={user}
          isAdminOpen={isAdminOpen}
          onToggleAdmin={() => setIsAdminOpen(!isAdminOpen)}
          onClose={closeMenu}
          onLogout={logout}
        />
      )}
    </nav>
  );
}
