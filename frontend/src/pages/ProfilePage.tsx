import { useAuthStore } from '@/store/authStore';

export default function ProfilePage() {
  const user = useAuthStore((state) => state.user);

  if (!user) return null;

  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-2xl mx-auto">
        <div className="card">
          <h1 className="text-3xl font-bold mb-6">Profil</h1>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-600">
                Nom d'utilisateur
              </label>
              <p className="text-lg">{user.username}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-600">
                Email
              </label>
              <p className="text-lg">{user.email}</p>
            </div>

            <div className="grid grid-cols-3 gap-4 pt-4 border-t">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary-600">
                  {user.total_games_played}
                </div>
                <div className="text-sm text-gray-600">Parties jouées</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {user.total_wins}
                </div>
                <div className="text-sm text-gray-600">Victoires</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {user.win_rate.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">Taux de victoire</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
