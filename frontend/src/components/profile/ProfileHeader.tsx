import type { User } from '@/types';
import type { UserDetailedStats } from '@/types';
import { formatLocalDate } from '@/utils/format';

interface Props {
  user: User;
  avatarPreview: string | null;
  detailedStats: UserDetailedStats | null;
  onAchievementsClick: () => void;
}

export default function ProfileHeader({ user, avatarPreview, detailedStats, onAchievementsClick }: Props) {
  return (
    <div className="card mb-6">
      <div className="flex flex-col sm:flex-row items-center gap-6">
        {/* Avatar */}
        <div className="w-24 h-24 rounded-full overflow-hidden ring-4 ring-primary-200 shadow-md flex-shrink-0">
          {avatarPreview ? (
            <img src={avatarPreview} alt="Avatar" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full bg-primary-100 flex items-center justify-center">
              <span className="text-primary-500 text-4xl font-bold select-none">
                {user.username.charAt(0).toUpperCase()}
              </span>
            </div>
          )}
        </div>

        {/* Identity */}
        <div className="flex-1 text-center sm:text-left">
          <h1 className="text-3xl font-bold text-dark">{user.username}</h1>
          <p className="text-gray-500 text-sm mt-1">
            Membre depuis{' '}
            {formatLocalDate(user.created_at, { month: 'long', year: 'numeric' })}
          </p>
          <div className="flex flex-wrap justify-center sm:justify-start gap-2 mt-3">
            <span className="flex items-center gap-1.5 text-sm bg-white px-3 py-1 rounded-full border border-cream-300 shadow-sm">
              <span className="font-bold text-primary-600">{user.total_games_played}</span>
              <span className="text-gray-500">parties</span>
            </span>
            <span className="flex items-center gap-1.5 text-sm bg-white px-3 py-1 rounded-full border border-cream-300 shadow-sm">
              <span className="font-bold text-green-600">{user.total_wins}</span>
              <span className="text-gray-500">victoires</span>
            </span>
            <span className="flex items-center gap-1.5 text-sm bg-white px-3 py-1 rounded-full border border-cream-300 shadow-sm">
              <span className="font-bold text-primary-600">{user.total_points}</span>
              <span className="text-gray-500">points</span>
            </span>
            {user.coins_balance !== undefined && (
              <span className="flex items-center gap-1.5 text-sm bg-primary-50 px-3 py-1 rounded-full border border-primary-200">
                <span>🪙</span>
                <span className="font-bold text-primary-700">{user.coins_balance}</span>
              </span>
            )}
          </div>
        </div>

        {/* Achievements quick access */}
        {detailedStats && (
          <button
            onClick={onAchievementsClick}
            className="flex-shrink-0 text-center bg-primary-50 hover:bg-primary-100 rounded-xl p-4 border border-primary-200 transition-colors"
          >
            <div className="text-3xl mb-1">🏆</div>
            <div className="text-xl font-bold text-primary-700">
              {detailedStats.achievements_unlocked}/{detailedStats.achievements_total}
            </div>
            <div className="text-xs text-gray-500 mt-0.5">Succès</div>
          </button>
        )}
      </div>
    </div>
  );
}
