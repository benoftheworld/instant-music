import { Link } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { useLogout } from '@/hooks/useAuth';

export default function Navbar() {
  const { isAuthenticated, user } = useAuthStore();
  const logout = useLogout();

  return (
    <nav className="bg-primary-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="text-2xl font-bold">
            🎵 InstantMusic
          </Link>

          <div className="flex items-center gap-6">
            {isAuthenticated ? (
              <>
                <Link to="/history" className="hover:text-primary-200 transition-colors">
                  Historique
                </Link>
                <Link to="/profile" className="hover:text-primary-200 transition-colors">
                  {user?.username}
                </Link>
                <button
                  onClick={logout}
                  className="btn btn-secondary"
                >
                  Déconnexion
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn-secondary">
                  Connexion
                </Link>
                <Link to="/register" className="btn bg-white text-primary-600 hover:bg-gray-100">
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
