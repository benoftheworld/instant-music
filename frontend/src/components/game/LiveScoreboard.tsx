import { getMediaUrl } from '@/services/api';
import type { GamePlayer } from '@/types';

interface LiveScoreboardProps {
  players: GamePlayer[];
}

const LiveScoreboard = ({ players }: LiveScoreboardProps) => {
  // Sort players by score (highest first)
  const sortedPlayers = [...players].sort((a, b) => b.score - a.score);

  const getMedalEmoji = (index: number) => {
    switch (index) {
      case 0:
        return '🥇';
      case 1:
        return '🥈';
      case 2:
        return '🥉';
      default:
        return `${index + 1}.`;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-xl p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
        <span className="mr-2">🏆</span>
        Classement
      </h2>

      <div className="space-y-3">
        {sortedPlayers.map((player, index) => (
          <div
            key={player.id}
            className={`flex items-center justify-between p-3 rounded-lg transition-all ${
              index === 0
                ? 'bg-primary-100 border-2 border-primary-400'
                : 'bg-cream-100 border-2 border-cream-300'
            }`}
          >
            <div className="flex items-center space-x-3">
              {/* Rank/Medal */}
              <div className="text-2xl font-bold w-8">
                {getMedalEmoji(index)}
              </div>

              {/* Avatar */}
              {player.avatar ? (
                <img
                  src={getMediaUrl(player.avatar)}
                  alt={player.username}
                  className="w-10 h-10 rounded-full"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white font-bold">
                  {player.username.charAt(0).toUpperCase()}
                </div>
              )}

              {/* Username */}
              <div>
                <p className="font-semibold text-dark flex items-center gap-1">
                  {player.username}
                  {(player.consecutive_correct ?? 0) >= 2 && (
                    <span className="text-xs font-bold text-primary-500">
                      🔥×{player.consecutive_correct}
                    </span>
                  )}
                </p>
                {!player.is_connected && (
                  <p className="text-xs text-gray-500">Déconnecté</p>
                )}
              </div>
            </div>

            {/* Score */}
            <div className="text-right">
              <p className="text-2xl font-bold text-primary-600">{player.score}</p>
              <p className="text-xs text-dark-300">points</p>
            </div>
          </div>
        ))}
      </div>

      {players.length === 0 && (
        <div className="text-center text-dark-300 py-8">
          Aucun joueur
        </div>
      )}
    </div>
  );
};

export default LiveScoreboard;
