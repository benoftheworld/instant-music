import { Link } from 'react-router-dom';
import { getMediaUrl } from '@/services/api';
import { PageLoader, Avatar } from '@/components/ui';
import { StatCard, MiniStat } from '@/components/ui/StatCard';
import { usePublicProfilePage } from '@/hooks/pages/usePublicProfilePage';
import { formatLocalDate } from '@/utils/format';

export default function PublicProfilePage() {
  const { navigate, profile, loading, error } = usePublicProfilePage();

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <PageLoader />
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="container mx-auto px-4 py-8 text-center">
        <p className="text-red-600 text-lg">{error || 'Profil introuvable.'}</p>
        <button onClick={() => navigate(-1)} className="mt-4 text-primary-600 hover:underline">
          ← Retour
        </button>
      </div>
    );
  }

  const { stats } = profile;

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      {/* Header */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">
        <div className="flex items-center gap-5">
          {profile.avatar ? (
            <img
              src={getMediaUrl(profile.avatar)}
              alt={profile.username}
              className="w-20 h-20 rounded-full object-cover ring-4 ring-primary-100"
            />
          ) : (
            <Avatar src={null} username={profile.username} size="xl" className="ring-4 ring-primary-100" />
          )}
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold truncate">{profile.username}</h1>
            {profile.team && (
              <Link
                to={`/teams/${profile.team.id}`}
                className="text-sm text-primary-500 hover:underline"
              >
                🛡️ {profile.team.name}
              </Link>
            )}
            <p className="text-sm text-gray-400 mt-1">
              Membre depuis le {formatLocalDate(profile.date_joined, { year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>
        </div>
      </div>

      {/* Statistiques */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-700">📊 Statistiques</h2>

        {/* Main stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard icon="🎮" label="Parties jouées" value={stats.total_games_played} textColor="text-primary-600" bgClass="bg-primary-50 border-primary-200" />
          <StatCard icon="🏆" label="Victoires" value={stats.total_wins} textColor="text-primary-600" bgClass="bg-primary-50 border-primary-200" />
          <StatCard icon="⭐" label="Points totaux" value={stats.total_points.toLocaleString()} textColor="text-primary-600" bgClass="bg-primary-50 border-primary-200" />
          <StatCard icon="📈" label="Taux de victoire" value={`${stats.win_rate}%`} textColor="text-primary-600" bgClass="bg-primary-50 border-primary-200" />
        </div>

        {/* Detailed stats */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <MiniStat label="Meilleur score" value={String(stats.best_score)} />
          <MiniStat label="Score moyen" value={String(stats.avg_score_per_game)} />
          <MiniStat label="Précision" value={`${stats.accuracy}%`} highlight />
          <MiniStat label="Temps moy. réponse" value={`${stats.avg_response_time}s`} />
          <MiniStat label="Succès débloqués" value={`${stats.achievements_unlocked}/${stats.achievements_total}`} />
        </div>
      </div>
    </div>
  );
}

/* ── Sub-components ────────────────────────────────────────────────────── */
