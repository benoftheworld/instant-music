import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { statsService } from '@/services/statsService';
import { getMediaUrl } from '@/services/api';
import type { UserPublicProfile } from '@/types';

export default function PublicProfilePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const currentUser = useAuthStore((s) => s.user);
  const [profile, setProfile] = useState<UserPublicProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Redirect to own profile page if viewing self
  useEffect(() => {
    if (id && currentUser && id === String(currentUser.id)) {
      navigate('/profile', { replace: true });
    }
  }, [id, currentUser, navigate]);

  useEffect(() => {
    if (!id) return;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const profileData = await statsService.getUserStats(id);
        setProfile(profileData);
      } catch {
        setError('Impossible de charger le profil.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
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
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-3xl font-bold ring-4 ring-primary-100">
              {profile.username.charAt(0).toUpperCase()}
            </div>
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
              Membre depuis le {new Date(profile.date_joined).toLocaleDateString('fr-FR', { year: 'numeric', month: 'long', day: 'numeric' })}
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

function StatCard({
  icon,
  label,
  value,
  textColor,
  bgClass,
}: {
  icon: string;
  label: string;
  value: number | string;
  textColor: string;
  bgClass: string;
}) {
  return (
    <div className={`rounded-xl border p-4 text-center ${bgClass}`}>
      <div className="text-2xl mb-2">{icon}</div>
      <div className={`text-2xl font-bold ${textColor}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-1 font-medium leading-tight">{label}</div>
    </div>
  );
}

function MiniStat({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div
      className={`rounded-lg p-3 text-center border ${
        highlight ? 'bg-primary-50 border-primary-200' : 'bg-cream-100 border-cream-300'
      }`}
    >
      <div className={`text-xl font-bold ${highlight ? 'text-primary-600' : 'text-dark'}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-0.5">{label}</div>
    </div>
  );
}
