import { Link } from 'react-router-dom';
import {
  IconLeaderboard,
  IconFriends,
  IconTeams,
  IconHistory,
  IconShop,
  IconAdmin,
  IconChevron,
  ADMIN_MONITORING_LINKS,
  getAdminHref,
  UserAvatar,
  MOBILE_LINK_CLASS,
} from './navbarShared';

interface MobileNavProps {
  isAuthenticated: boolean;
  user: any;
  isAdminOpen: boolean;
  onToggleAdmin: () => void;
  onClose: () => void;
  onLogout: () => void;
}

export default function MobileNav({
  isAuthenticated,
  user,
  isAdminOpen,
  onToggleAdmin,
  onClose,
  onLogout,
}: MobileNavProps) {
  return (
    <div id="mobile-menu" className="md:hidden border-t border-primary-700 bg-dark">
      <div className="container mx-auto px-4 py-3 flex flex-col gap-1">
        {isAuthenticated ? (
          <>
            <Link to="/leaderboard" onClick={onClose} className={MOBILE_LINK_CLASS}>
              <IconLeaderboard />Classement
            </Link>
            <Link to="/friends" onClick={onClose} className={MOBILE_LINK_CLASS}>
              <IconFriends />Amis
            </Link>
            <Link to="/teams" onClick={onClose} className={MOBILE_LINK_CLASS}>
              <IconTeams />Équipes
            </Link>
            <Link to="/history" onClick={onClose} className={MOBILE_LINK_CLASS}>
              <IconHistory />Historique
            </Link>
            <Link to="/shop" onClick={onClose} className={`${MOBILE_LINK_CLASS} text-yellow-400`}>
              <IconShop />Boutique
              {(user?.coins_balance ?? 0) > 0 && (
                <span className="ml-auto text-xs bg-yellow-500 text-dark font-bold rounded-full px-1.5 py-0.5 leading-none">
                  {user?.coins_balance} pièces
                </span>
              )}
            </Link>
            <Link to="/profile" onClick={onClose} className={MOBILE_LINK_CLASS}>
              <UserAvatar user={user} size="w-5 h-5" />{user?.username}
            </Link>

            {user?.is_staff && (
              <>
                <button
                  className={`${MOBILE_LINK_CLASS} w-full justify-between`}
                  onClick={onToggleAdmin}
                >
                  <span className="flex items-center gap-3">
                    <IconAdmin />Administration
                  </span>
                  <IconChevron open={isAdminOpen} />
                </button>
                {isAdminOpen && (
                  <div className="ml-8 flex flex-col gap-1">
                    {ADMIN_MONITORING_LINKS.map(({ href, label, colorClass, icon }) => (
                      <a key={href} href={href} target="_blank" rel="noopener noreferrer" onClick={onClose} className={MOBILE_LINK_CLASS}>
                        <svg xmlns="http://www.w3.org/2000/svg" className={`w-4 h-4 shrink-0 ${colorClass}`} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">{icon}</svg>
                        {label}
                      </a>
                    ))}
                    <a href={getAdminHref()} target="_blank" rel="noopener noreferrer" onClick={onClose} className={MOBILE_LINK_CLASS}>
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
                onClick={() => { onClose(); onLogout(); }}
                className="w-full btn bg-cream-100 text-dark hover:bg-cream-200"
              >
                Déconnexion
              </button>
            </div>
          </>
        ) : (
          <div className="flex flex-col gap-2 pt-2 pb-1">
            <Link to="/login" onClick={onClose} className="btn bg-transparent border-2 border-cream-100 text-cream-100 hover:bg-cream-100 hover:text-dark text-center">
              Connexion
            </Link>
            <Link to="/register" onClick={onClose} className="btn bg-primary-500 text-white hover:bg-primary-600 text-center">
              Inscription
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
