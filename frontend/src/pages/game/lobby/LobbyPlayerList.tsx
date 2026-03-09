import { Game } from '../../../types';
import { getMediaUrl } from '../../../services/api';

interface LobbyPlayerListProps {
  game: Game;
}

export default function LobbyPlayerList({ game }: LobbyPlayerListProps) {
  return (
    <div className="lg:col-span-1">
      <div className="card">
        <h2 className="text-xl font-bold mb-4">
          Joueurs ({game.player_count}/{game.max_players})
        </h2>
        <div className="space-y-3">
          {game.players.map((player) => (
            <div
              key={player.id}
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
            >
              {player.avatar ? (
                <img
                  src={getMediaUrl(player.avatar)}
                  alt={player.username}
                  className="w-10 h-10 rounded-full object-cover"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                  <span className="text-primary-600 font-semibold">
                    {player.username.charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="font-semibold truncate">
                  {player.username}
                  {player.user === game.host && (
                    <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                      Hôte
                    </span>
                  )}
                </p>
              </div>
              <div className={`w-2 h-2 rounded-full ${
                player.is_connected ? 'bg-green-500' : 'bg-gray-300'
              }`}></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
