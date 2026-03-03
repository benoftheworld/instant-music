import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { useLogout } from '@/hooks/useAuth';
import { getMediaUrl } from '@/services/api';
import { authService } from '@/services/authService';
import NotificationBell from './NotificationBell';

// ── Icônes réutilisables ──────────────────────────────────────────────────────

function IconLeaderboard() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M22,7H16.333V4a1,1,0,0,0-1-1H8.667a1,1,0,0,0-1,1v7H2a1,1,0,0,0-1,1v8a1,1,0,0,0,1,1H22a1,1,0,0,0,1-1V8A1,1,0,0,0,22,7ZM7.667,19H3V13H7.667Zm6.666,0H9.667V5h4.666ZM21,19H16.333V9H21Z"/>
    </svg>
  );
}

function IconFriends() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87M16 11a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
  );
}

function IconTeams() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v18M19 7l-7 4-7-4" />
    </svg>
  );
}

function IconHistory() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function IconShop() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1.41 16.09V20h-2.67v-1.93c-1.71-.36-3.16-1.46-3.27-3.4h1.96c.1 1.05.82 1.87 2.65 1.87 1.96 0 2.4-.98 2.4-1.59 0-.83-.44-1.61-2.67-2.14-2.48-.6-4.18-1.62-4.18-3.67 0-1.72 1.39-2.84 3.11-3.21V4h2.67v1.95c1.86.45 2.79 1.86 2.85 3.39H14.3c-.05-1.11-.64-1.87-2.22-1.87-1.5 0-2.4.68-2.4 1.64 0 .84.65 1.39 2.67 1.91s4.18 1.39 4.18 3.91c-.01 1.83-1.38 2.83-3.12 3.16z"/>
    </svg>
  );
}

function IconAdmin() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  );
}

function IconChevron({ open }: { open: boolean }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
    </svg>
  );
}

// ── Dropdown Administration (desktop) ────────────────────────────────────────

function AdminDropdown() {
  const adminLinks = [
    { href: '/grafana/', label: 'Grafana', iconColor: 'text-orange-400', icon: <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/> },
    { href: '/prometheus/', label: 'Prometheus', iconColor: 'text-red-400', icon: <path d="M12 2a10 10 0 100 20A10 10 0 0012 2zm0 18a8 8 0 110-16 8 8 0 010 16zm-1-5h2v2h-2zm0-8h2v6h-2z"/> },
    { href: '/kibana/', label: 'Kibana', iconColor: 'text-blue-400', icon: <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/> },
  ];

  return (
    <div className="absolute right-0 top-full mt-1 w-52 bg-dark border border-primary-500 rounded-md shadow-xl z-50 hidden group-hover:block">
      {adminLinks.map(({ href, label, iconColor, icon }, i) => (
        <a
          key={href}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className={`flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-primary-600 hover:text-white transition-colors ${i === 0 ? 'rounded-t-md' : ''}`}
        >
          <svg xmlns="http://www.w3.org/2000/svg" className={`w-4 h-4 shrink-0 ${iconColor}`} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">{icon}</svg>
          {label}
        </a>
      ))}
      <div className="border-t border-primary-700 my-1" />
      <a
        href="/admin/"
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-primary-600 hover:text-white transition-colors rounded-b-md"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-gray-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        Admin Django
      </a>
    </div>
  );
}

// ── Composant principal ───────────────────────────────────────────────────────

export default function Navbar() {
  const { isAuthenticated, user, updateUser } = useAuthStore();
  const logout = useLogout();
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isAdminOpen, setIsAdminOpen] = useState(false);

  // Ferme le menu mobile à chaque changement de route
  useEffect(() => {
    setIsMenuOpen(false);
    setIsAdminOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!isAuthenticated) return;
    authService.getCurrentUser().then(updateUser).catch(() => {});
  }, [isAuthenticated]);

  const closeMenu = () => setIsMenuOpen(false);

  const desktopLinkClass = 'hover:text-primary-400 transition-colors flex items-center gap-2';
  const mobileLinkClass = 'flex items-center gap-3 px-3 py-2.5 rounded-md hover:bg-dark-600 hover:text-primary-400 transition-colors text-sm font-medium';

  const UserAvatar = ({ size = 'w-6 h-6' }: { size?: string }) =>
    user?.avatar ? (
      <img src={getMediaUrl(user.avatar)} alt={user.username} className={`${size} rounded-full object-cover shrink-0`} />
    ) : (
      <div className={`${size} rounded-full bg-gray-300 flex items-center justify-center text-xs text-gray-700 shrink-0`}>
        {user?.username?.charAt(0)?.toUpperCase()}
      </div>
    );

  return (
    <nav className="bg-dark text-cream-100 shadow-lg border-b-4 border-primary-500">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">

          {/* ── Logo ── */}
          <Link to="/" className="text-2xl font-bold hover:text-primary-400 transition-colors flex items-center shrink-0">
            <span className="text-primary-600">Instant</span>Music
          </Link>

          {/* ── Navigation desktop (md+) ── */}
          <div className="hidden md:flex items-center gap-6">
            <Link to="/leaderboard" className={desktopLinkClass}>
              <IconLeaderboard /><span>Classement</span>
            </Link>

            {isAuthenticated ? (
              <>
                <Link to="/friends" className={desktopLinkClass}>
                  <IconFriends /><span>Amis</span>
                </Link>
                <Link to="/teams" className={desktopLinkClass}>
                  <IconTeams /><span>Équipes</span>
                </Link>
                <Link to="/history" className={desktopLinkClass}>
                  <IconHistory /><span>Historique</span>
                </Link>
                <Link to="/shop" className={`${desktopLinkClass} text-yellow-400`}>
                  <IconShop /><span>Boutique</span>
                  {(user?.coins_balance ?? 0) > 0 && (
                    <span className="text-xs bg-yellow-500 text-dark font-bold rounded-full px-1.5 py-0.5 leading-none">
                      {user?.coins_balance}
                    </span>
                  )}
                </Link>

                {user?.is_staff && (
                  <div className="relative group">
                    <button className={`${desktopLinkClass} cursor-pointer`}>
                      <IconAdmin /><span>Administration</span>
                      <IconChevron open={false} />
                    </button>
                    <AdminDropdown />
                  </div>
                )}

                <NotificationBell />

                <Link to="/profile" className={desktopLinkClass}>
                  <UserAvatar /><span>{user?.username}</span>
                </Link>
                <button onClick={logout} className="btn bg-cream-100 text-dark hover:bg-cream-200">
                  Déconnexion
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn bg-transparent border-2 border-cream-100 text-cream-100 hover:bg-cream-100 hover:text-dark">
                  Connexion
                </Link>
                <Link to="/register" className="btn bg-primary-500 text-white hover:bg-primary-600">
                  Inscription
                </Link>
              </>
            )}
          </div>

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

      {/* ── Menu mobile déroulant ── */}
      {isMenuOpen && (
        <div id="mobile-menu" className="md:hidden border-t border-primary-700 bg-dark">
          <div className="container mx-auto px-4 py-3 flex flex-col gap-1">

            <Link to="/leaderboard" onClick={closeMenu} className={mobileLinkClass}>
              <IconLeaderboard />Classement
            </Link>

            {isAuthenticated ? (
              <>
                <Link to="/friends" onClick={closeMenu} className={mobileLinkClass}>
                  <IconFriends />Amis
                </Link>
                <Link to="/teams" onClick={closeMenu} className={mobileLinkClass}>
                  <IconTeams />Équipes
                </Link>
                <Link to="/history" onClick={closeMenu} className={mobileLinkClass}>
                  <IconHistory />Historique
                </Link>
                <Link to="/shop" onClick={closeMenu} className={`${mobileLinkClass} text-yellow-400`}>
                  <IconShop />Boutique
                  {(user?.coins_balance ?? 0) > 0 && (
                    <span className="ml-auto text-xs bg-yellow-500 text-dark font-bold rounded-full px-1.5 py-0.5 leading-none">
                      {user?.coins_balance} pièces
                    </span>
                  )}
                </Link>
                <Link to="/profile" onClick={closeMenu} className={mobileLinkClass}>
                  <UserAvatar size="w-5 h-5" />{user?.username}
                </Link>

                {user?.is_staff && (
                  <>
                    <button
                      className={`${mobileLinkClass} w-full justify-between`}
                      onClick={() => setIsAdminOpen(!isAdminOpen)}
                    >
                      <span className="flex items-center gap-3">
                        <IconAdmin />Administration
                      </span>
                      <IconChevron open={isAdminOpen} />
                    </button>
                    {isAdminOpen && (
                      <div className="ml-8 flex flex-col gap-1">
                        {[
                          { href: '/grafana/', label: 'Grafana', colorClass: 'text-orange-400', icon: <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/> },
                          { href: '/prometheus/', label: 'Prometheus', colorClass: 'text-red-400', icon: <path d="M12 2a10 10 0 100 20A10 10 0 0012 2zm0 18a8 8 0 110-16 8 8 0 010 16zm-1-5h2v2h-2zm0-8h2v6h-2z"/> },
                          { href: '/kibana/', label: 'Kibana', colorClass: 'text-blue-400', icon: <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/> },
                        ].map(({ href, label, colorClass, icon }) => (
                          <a key={href} href={href} target="_blank" rel="noopener noreferrer" onClick={closeMenu} className={mobileLinkClass}>
                            <svg xmlns="http://www.w3.org/2000/svg" className={`w-4 h-4 shrink-0 ${colorClass}`} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">{icon}</svg>
                            {label}
                          </a>
                        ))}
                        <a href="/admin/" target="_blank" rel="noopener noreferrer" onClick={closeMenu} className={mobileLinkClass}>
                          <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-gray-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          Admin Django
                        </a>
                      </div>
                    )}
                  </>
                )}

                <div className="pt-2 pb-1">
                  <button
                    onClick={() => { closeMenu(); logout(); }}
                    className="w-full btn bg-cream-100 text-dark hover:bg-cream-200"
                  >
                    Déconnexion
                  </button>
                </div>
              </>
            ) : (
              <div className="flex flex-col gap-2 pt-2 pb-1">
                <Link to="/login" onClick={closeMenu} className="btn bg-transparent border-2 border-cream-100 text-cream-100 hover:bg-cream-100 hover:text-dark text-center">
                  Connexion
                </Link>
                <Link to="/register" onClick={closeMenu} className="btn bg-primary-500 text-white hover:bg-primary-600 text-center">
                  Inscription
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
