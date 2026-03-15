import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { useLogin } from '@/hooks/useAuth';
import RecentGames from '@/components/home/RecentGames';
import TopPlayers from '@/components/home/TopPlayers';
import { Alert, FormField } from '@/components/ui';

export default function HomePage() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const loginMutation = useLogin();
  const [loginData, setLoginData] = useState({ username: '', password: '' });

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loginMutation.mutate(loginData);
  };

  return (
    <div className="container mx-auto px-4 py-16">
      <section aria-labelledby="hero-heading" className="text-center max-w-4xl mx-auto mb-12">
        <h1 id="hero-heading" className="text-5xl font-bold mb-6">
          Bienvenue sur <span className="text-primary-600">InstantMusic</span> !
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Jouez à des jeux musicaux multijoueurs en temps réel avec vos amis !
          Testez vos connaissances, chantez vos morceaux préférés et grimpez dans le classement !
        </p>

        <div className="grid md:grid-cols-3 gap-8 mb-12">
          <div className="card">
            <div className="text-4xl mb-4" aria-hidden="true">❓</div>
            <h3 className="text-xl font-bold mb-2">Quiz Musical</h3>
            <p className="text-gray-600">
              Testez vos connaissances musicales avec différents modes de jeu
            </p>
          </div>

          <div className="card">
            <div className="text-4xl mb-4" aria-hidden="true">🎤</div>
            <h3 className="text-xl font-bold mb-2">Karaoké</h3>
            <p className="text-gray-600">
              Chantez vos morceaux préférés avec les paroles synchronisées
            </p>
          </div>

          <div className="card">
            <div className="text-4xl mb-4" aria-hidden="true">👥</div>
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
              <div className="flex justify-center gap-4 mb-8">
                <Link to="/register" className="btn-primary text-lg px-8 py-3">
                  Commencer à jouer
                </Link>
              </div>

              {/* Formulaire de connexion rapide */}
              <div className="max-w-sm mx-auto card">
                <h2 className="text-xl font-bold mb-4 text-center">Déjà inscrit ?</h2>
                <form onSubmit={handleLoginSubmit} className="space-y-3">
                  <FormField
                    label="Identifiant (email ou pseudonyme)"
                    type="text"
                    value={loginData.username}
                    onChange={(e) => setLoginData((d) => ({ ...d, username: e.target.value }))}
                    required
                    autoComplete="username"
                  />
                  <FormField
                    label="Mot de passe"
                    type="password"
                    value={loginData.password}
                    onChange={(e) => setLoginData((d) => ({ ...d, password: e.target.value }))}
                    required
                    autoComplete="current-password"
                    labelRight={
                      <Link to="/forgot-password" className="text-sm text-primary-600 hover:underline">
                        Mot de passe oublié ?
                      </Link>
                    }
                  />
                  {loginMutation.isError && (
                    <Alert variant="error">Identifiants invalides</Alert>
                  )}
                  <button
                    type="submit"
                    disabled={loginMutation.isPending}
                    className="btn-secondary w-full"
                  >
                    {loginMutation.isPending ? 'Connexion…' : 'Se connecter'}
                  </button>
                </form>
              </div>
            </>
          )}
        </div>
      </section>

      {/* Recent Games and Leaderboard Section */}
      {isAuthenticated && (
        <div className="max-w-6xl mx-auto mt-16">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Recent Games */}
            <section aria-labelledby="recent-games-heading">
              <div className="flex items-center justify-between mb-4">
                <h2 id="recent-games-heading" className="text-2xl font-bold">Parties récentes</h2>
              </div>
              <RecentGames />
            </section>

            {/* Top Players */}
            <section aria-labelledby="top-players-heading">
              <div className="flex items-center justify-between mb-4">
                <h2 id="top-players-heading" className="text-2xl font-bold">Top joueurs</h2>
              </div>
              <TopPlayers />
            </section>
          </div>
        </div>
      )}
    </div>
  );
}
