import { getMediaUrl } from '@/services/api';

interface Player {
  id: string;
  username: string;
  score: number;
  rank: number | null;
  avatar?: string;
  is_connected?: boolean;
}

interface LiveScoreboardProps {
  players: Player[];
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
                ? 'bg-yellow-100 border-2 border-yellow-400'
                : 'bg-gray-50 border-2 border-gray-200'
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
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-blue-500 flex items-center justify-center text-white font-bold">
                  {player.username.charAt(0).toUpperCase()}
                </div>
              )}
              
              {/* Username */}
              <div>
                <p className="font-semibold text-gray-800">{player.username}</p>
                {!player.is_connected && (
                  <p className="text-xs text-gray-500">Déconnecté</p>
                )}
              </div>
            </div>
            
            {/* Score */}
            <div className="text-right">
              <p className="text-2xl font-bold text-blue-600">{player.score}</p>
              <p className="text-xs text-gray-500">points</p>
            </div>
          </div>
        ))}
      </div>
      
      {players.length === 0 && (
        <div className="text-center text-gray-500 py-8">
          Aucun joueur
        </div>
      )}
    </div>
  );
};

export default LiveScoreboard;
