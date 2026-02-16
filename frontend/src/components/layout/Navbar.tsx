import { Link } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { useLogout } from '@/hooks/useAuth';

export default function Navbar() {
  const { isAuthenticated, user } = useAuthStore();
  const logout = useLogout();

  return (
    <nav className="bg-dark text-cream-100 shadow-lg border-b-4 border-primary-500">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="text-2xl font-bold hover:text-primary-400 transition-colors">
            🎵 InstantMusic
          </Link>

          <div className="flex items-center gap-6">
            <Link to="/leaderboard" className="hover:text-primary-400 transition-colors">
              🏆 Classement
            </Link>
            {isAuthenticated ? (
              <>
                <Link to="/friends" className="hover:text-primary-400 transition-colors">
                  👥 Amis
                </Link>
                <Link to="/teams" className="hover:text-primary-400 transition-colors">
                  🎯 Équipes
                </Link>
                <Link to="/history" className="hover:text-primary-400 transition-colors">
                  Historique
                </Link>
                <Link to="/profile" className="hover:text-primary-400 transition-colors">
                  {user?.username}
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
