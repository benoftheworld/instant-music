import { Link } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { useLogout } from '@/hooks/useAuth';
import { getMediaUrl } from '@/services/api';

export default function Navbar() {
  const { isAuthenticated, user } = useAuthStore();
  const logout = useLogout();

  return (
    <nav className="bg-dark text-cream-100 shadow-lg border-b-4 border-primary-500">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="text-2xl font-bold hover:text-primary-400 transition-colors flex items-center">
            <span className="text-primary-600">Instant</span>Music
          </Link>

          <div className="flex items-center gap-6">
            <Link to="/leaderboard" className="hover:text-primary-400 transition-colors flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M22,7H16.333V4a1,1,0,0,0-1-1H8.667a1,1,0,0,0-1,1v7H2a1,1,0,0,0-1,1v8a1,1,0,0,0,1,1H22a1,1,0,0,0,1-1V8A1,1,0,0,0,22,7ZM7.667,19H3V13H7.667Zm6.666,0H9.667V5h4.666ZM21,19H16.333V9H21Z"/>
              </svg>
              <span>Classement</span>
            </Link>
            {isAuthenticated ? (
              <>
                <Link to="/friends" className="hover:text-primary-400 transition-colors flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87M16 11a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  <span>Amis</span>
                </Link>
                <Link to="/teams" className="hover:text-primary-400 transition-colors flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v18M19 7l-7 4-7-4" />
                  </svg>
                  <span>Équipes</span>
                </Link>
                <Link to="/history" className="hover:text-primary-400 transition-colors flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Historique</span>
                </Link>
                <Link to="/profile" className="hover:text-primary-400 transition-colors flex items-center gap-2">
                  {user?.avatar ? (
                    <img
                      src={getMediaUrl(user.avatar)}
                      alt={user.username}
                      className="w-6 h-6 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center text-xs text-gray-700">
                      {user?.username?.charAt(0)?.toUpperCase()}
                    </div>
                  )}
                  <span>{user?.username}</span>
                </Link>
                <button
                  onClick={logout}
                  className="btn bg-cream-100 text-dark hover:bg-cream-200"
                >
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
        </div>
      </div>
    </nav>
  );
}
