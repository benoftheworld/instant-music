import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { statsService } from '@/services/statsService';
import { achievementService } from '@/services/achievementService';
import { getMediaUrl } from '@/services/api';
import type { UserPublicProfile, UserAchievement } from '@/types';

const ACHIEVEMENT_ICONS: Record<string, string> = {
  games_played: '🎮',
  wins: '🏆',
  points: '⭐',
  perfect_round: '💯',
  win_streak: '🔥',
};

function getAchievementIcon(conditionType: string): string {
  return ACHIEVEMENT_ICONS[conditionType] ?? '🎵';
}

export default function PublicProfilePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const currentUser = useAuthStore((s) => s.user);
  const [profile, setProfile] = useState<UserPublicProfile | null>(null);
  const [achievements, setAchievements] = useState<UserAchievement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'stats' | 'achievements'>('stats');

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
        const [profileData, achievementsData] = await Promise.all([
          statsService.getUserStats(id),
          achievementService.getByUser(id),
        ]);
        setProfile(profileData);
        setAchievements(achievementsData);
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
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-5 mb-8">
        {profile.avatar ? (
          <img
            src={getMediaUrl(profile.avatar)}
            alt={profile.username}
            className="w-24 h-24 rounded-full object-cover ring-4 ring-primary-200"
          />
        ) : (
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-purple-400 to-blue-500 flex items-center justify-center text-white text-4xl font-bold ring-4 ring-primary-200">
            {profile.username.charAt(0).toUpperCase()}
          </div>
        )}
        <div>
          <h1 className="text-3xl font-bold">{profile.username}</h1>
          {profile.team && (
            <Link
              to={`/teams/${profile.team.id}`}
              className="text-sm text-primary-500 hover:underline"
            >
              🛡️ {profile.team.name}
            </Link>
          )}
          <p className="text-sm text-gray-500 mt-1">
            Membre depuis le {new Date(profile.date_joined).toLocaleDateString('fr-FR', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200 pb-2">
        <button
          onClick={() => setActiveTab('stats')}
          className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
            activeTab === 'stats'
              ? 'bg-primary-500 text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          📊 Statistiques
        </button>
        <button
          onClick={() => setActiveTab('achievements')}
          className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
            activeTab === 'achievements'
              ? 'bg-primary-500 text-white'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          🏆 Succès ({achievements.length})
        </button>
      </div>

      {/* Stats Tab */}
      {activeTab === 'stats' && (
        <div className="space-y-6">
          {/* Main stats grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatCard icon="🎮" label="Parties jouées" value={stats.total_games_played} textColor="text-blue-600" bgClass="bg-blue-50 border-blue-200" />
            <StatCard icon="🏆" label="Victoires" value={stats.total_wins} textColor="text-yellow-600" bgClass="bg-yellow-50 border-yellow-200" />
            <StatCard icon="⭐" label="Points totaux" value={stats.total_points.toLocaleString()} textColor="text-primary-600" bgClass="bg-primary-50 border-primary-200" />
            <StatCard icon="📈" label="Taux de victoire" value={`${stats.win_rate}%`} textColor="text-green-600" bgClass="bg-green-50 border-green-200" />
          </div>

          {/* Detailed stats */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <MiniStat label="Meilleur score" value={String(stats.best_score)} />
            <MiniStat label="Score moyen" value={String(stats.avg_score_per_game)} />
            <MiniStat label="Précision" value={`${stats.accuracy}%`} highlight />
            <MiniStat label="Temps moy. réponse" value={`${stats.avg_response_time}s`} />
            <MiniStat label="Succès débloqués" value={`${stats.achievements_unlocked}/${stats.achievements_total}`} highlight />
          </div>
        </div>
      )}

      {/* Achievements Tab */}
      {activeTab === 'achievements' && (
        <div>
          {achievements.length === 0 ? (
            <p className="text-gray-500 text-center py-8">Aucun succès débloqué.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {achievements.map((ua) => (
                <div
                  key={ua.id}
                  className="flex items-center gap-3 p-4 rounded-xl bg-yellow-50 border border-yellow-200"
                >
                  <div className="text-3xl">
                    {ua.achievement.icon ? (
                      <img src={getMediaUrl(ua.achievement.icon)} alt="" className="w-10 h-10" />
                    ) : (
                      getAchievementIcon(ua.achievement.condition_type)
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm truncate">{ua.achievement.name}</p>
                    <p className="text-xs text-gray-500 truncate">{ua.achievement.description}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Débloqué le {new Date(ua.unlocked_at).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                  <div className="text-xs font-bold text-yellow-600">{ua.achievement.points} 🪙</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
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
