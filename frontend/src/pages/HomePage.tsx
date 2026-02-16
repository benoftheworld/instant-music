import { Link } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import RecentGames from '@/components/home/RecentGames';
import TopPlayers from '@/components/home/TopPlayers';

export default function HomePage() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return (
    <div className="container mx-auto px-4 py-16">
      <div className="text-center max-w-4xl mx-auto mb-12">
        <h1 className="text-5xl font-bold mb-6">
          Bienvenue sur InstantMusic 🎵
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Jouez à des jeux musicaux multijoueurs en temps réel avec vos amis !
        </p>

        <div className="grid md:grid-cols-3 gap-8 mb-12">
          <div className="card">
            <div className="text-4xl mb-4">❓</div>
            <h3 className="text-xl font-bold mb-2">Quiz Musical</h3>
            <p className="text-gray-600">
              Testez vos connaissances musicales avec différents modes de jeu
            </p>
          </div>

          <div className="card">
            <div className="text-4xl mb-4">🎤</div>
            <h3 className="text-xl font-bold mb-2">Karaoké</h3>
            <p className="text-gray-600">
              Chantez vos morceaux préférés et montrez votre talent
            </p>
          </div>

          <div className="card">
            <div className="text-4xl mb-4">👥</div>
            <h3 className="text-xl font-bold mb-2">Multijoueur</h3>
            <p className="text-gray-600">
              Affrontez vos amis en temps réel dans des parties endiablées
            </p>
          </div>
        </div>

        <div className="flex justify-center gap-4">
          {isAuthenticated ? (
            <>
              <Link to="/game/create" className="btn-primary text-lg px-8 py-3">
                Créer une partie
              </Link>
              <Link to="/game/join" className="btn-secondary text-lg px-8 py-3">
                Rejoindre une partie
              </Link>
            </>
          ) : (
            <>
              <Link to="/register" className="btn-primary text-lg px-8 py-3">
                Commencer à jouer
              </Link>
              <Link to="/login" className="btn-secondary text-lg px-8 py-3">
                Se connecter
              </Link>
            </>
          )}
        </div>
      </div>

      {/* Recent Games and Leaderboard Section */}
      {isAuthenticated && (
        <div className="max-w-6xl mx-auto mt-16">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Recent Games */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold">Parties récentes</h2>
              </div>
              <RecentGames />
            </div>

            {/* Top Players */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold">Top joueurs</h2>
              </div>
              <TopPlayers />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
