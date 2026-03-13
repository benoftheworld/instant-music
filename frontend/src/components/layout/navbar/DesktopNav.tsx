import { Link } from 'react-router-dom';
import NotificationBell from '../NotificationBell';
import {
  IconLeaderboard,
  IconFriends,
  IconTeams,
  IconHistory,
  IconShop,
  IconAdmin,
  IconChevron,
  AdminDropdown,
  UserAvatar,
  DESKTOP_LINK_CLASS,
} from './navbarShared';

interface DesktopNavProps {
  isAuthenticated: boolean;
  user: any;
  onLogout: () => void;
}

export default function DesktopNav({ isAuthenticated, user, onLogout }: DesktopNavProps) {
  return (
    <div className="hidden md:flex items-center gap-6">
      <Link to="/leaderboard" className={DESKTOP_LINK_CLASS}>
        <IconLeaderboard /><span>Classement</span>
      </Link>

      {isAuthenticated ? (
        <>
          <Link to="/friends" className={DESKTOP_LINK_CLASS}>
            <IconFriends /><span>Amis</span>
          </Link>
          <Link to="/teams" className={DESKTOP_LINK_CLASS}>
            <IconTeams /><span>Équipes</span>
          </Link>
          <Link to="/history" className={DESKTOP_LINK_CLASS}>
            <IconHistory /><span>Historique</span>
          </Link>
          <Link to="/shop" className={`${DESKTOP_LINK_CLASS} text-yellow-400`}>
            <IconShop /><span>Boutique</span>
            {(user?.coins_balance ?? 0) > 0 && (
              <span className="text-xs bg-yellow-500 text-dark font-bold rounded-full px-1.5 py-0.5 leading-none">
                {user?.coins_balance}
              </span>
            )}
          </Link>

          {user?.is_staff && (
            <div className="relative group">
              <button className={`${DESKTOP_LINK_CLASS} cursor-pointer`}>
                <IconAdmin /><span>Administration</span>
                <IconChevron open={false} />
              </button>
              <AdminDropdown />
            </div>
          )}

          <NotificationBell />

          <Link to="/profile" className={DESKTOP_LINK_CLASS}>
            <UserAvatar user={user} /><span>{user?.username}</span>
          </Link>
          <button onClick={onLogout} className="btn bg-cream-100 text-dark hover:bg-cream-200">
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
  );
}
