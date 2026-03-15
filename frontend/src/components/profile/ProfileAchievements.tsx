import type { Achievement } from '@/types';
import { formatLocalDate } from '@/utils/format';

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

function SectionTitle({ icon, title }: { icon: string; title: string }) {
  return (
    <h2 className="text-xl font-bold text-dark flex items-center gap-2">
      <span>{icon}</span>
      {title}
    </h2>
  );
}

interface Props {
  achievements: Achievement[];
  achievementsLoading: boolean;
  achievementFilter: 'all' | 'unlocked' | 'locked';
  setAchievementFilter: (f: 'all' | 'unlocked' | 'locked') => void;
  filteredAchievements: Achievement[];
  unlockedCount: number;
  getAchievementProgress: (a: Achievement) => number;
  getAchievementProgressLabel: (a: Achievement) => string | null;
}

export default function ProfileAchievements({
  achievements,
  achievementsLoading,
  achievementFilter,
  setAchievementFilter,
  filteredAchievements,
  unlockedCount,
  getAchievementProgress,
  getAchievementProgressLabel,
}: Props) {
  return (
    <div className="card">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <SectionTitle icon="" title={`Succès (${unlockedCount}/${achievements.length})`} />
        <div className="flex gap-2">
          {(
            [
              { id: 'all', label: 'Tous' },
              { id: 'unlocked', label: '✅ Débloqués' },
              { id: 'locked', label: '🔒 Verrouillés' },
            ] as const
          ).map((f) => (
            <button
              key={f.id}
              onClick={() => setAchievementFilter(f.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                achievementFilter === f.id
                  ? 'bg-primary-500 text-white'
                  : 'bg-cream-100 text-gray-600 hover:bg-cream-200'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {achievementsLoading ? (
        <div className="text-center py-12 text-gray-400">
          <div className="text-4xl mb-3">⏳</div>
          <p>Chargement des succès…</p>
        </div>
      ) : filteredAchievements.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <div className="text-4xl mb-3">🏅</div>
          <p>Aucun succès dans cette catégorie</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAchievements.map((achievement) => {
            const progress = getAchievementProgress(achievement);
            const progressLabel = getAchievementProgressLabel(achievement);
            return (
              <div
                key={achievement.id}
                className={`rounded-xl p-4 border-2 transition-all ${
                  achievement.unlocked
                    ? 'border-yellow-300 bg-gradient-to-br from-yellow-50 to-amber-50 shadow-sm'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`text-3xl flex-shrink-0 ${achievement.unlocked ? '' : 'grayscale opacity-50'}`}>
                    {getAchievementIcon(achievement.condition_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h3
                        className={`font-bold text-sm leading-tight ${
                          achievement.unlocked ? 'text-yellow-800' : 'text-gray-500'
                        }`}
                      >
                        {achievement.name}
                      </h3>
                      {achievement.unlocked && (
                        <svg className="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5 leading-relaxed">{achievement.description}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span
                        className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                          achievement.unlocked
                            ? 'bg-yellow-200 text-yellow-800'
                            : 'bg-gray-200 text-gray-500'
                        }`}
                      >
                        {achievement.points} pts
                      </span>
                      {achievement.unlocked && achievement.unlocked_at ? (
                        <span className="text-xs text-gray-400">
                          {formatLocalDate(achievement.unlocked_at)}
                        </span>
                      ) : progressLabel ? (
                        <span className="text-xs text-gray-400">{progressLabel}</span>
                      ) : null}
                    </div>
                    {!achievement.unlocked && progress > 0 && (
                      <div className="mt-2 h-1.5 rounded-full bg-gray-200 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-primary-400 transition-all"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
