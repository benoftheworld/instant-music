import { Game } from '../../../types';

interface LobbyActionsProps {
  game: Game;
  isHost: boolean;
  isSolo: boolean;
  startingGame: boolean;
  startError: string | null;
  onLeave: () => void;
  onStart: () => void;
  onInvite: () => void;
}

export default function LobbyActions({
  game,
  isHost,
  isSolo,
  startingGame,
  startError,
  onLeave,
  onStart,
  onInvite,
}: LobbyActionsProps) {
  return (
    <div className="card">
      <div className="flex items-center justify-between gap-4">
        <button
          onClick={onLeave}
          className="btn-secondary flex-1"
        >
          Quitter
        </button>
        {isHost && !isSolo && (
          <button
            onClick={onInvite}
            className="btn-secondary flex items-center gap-2"
            title="Inviter des amis"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
            Inviter
          </button>
        )}
        {isHost && (
          <button
            onClick={onStart}
            className="btn-primary flex-1"
            disabled={(isSolo ? game.player_count < 1 : game.player_count < 2) || startingGame}
          >
            {startingGame ? 'Démarrage...' : 'Démarrer la partie'}
          </button>
        )}
      </div>
      {isHost && !isSolo && game.player_count < 2 && (
        <p className="text-sm text-orange-600 text-center mt-2">
          Il faut au moins 2 joueurs pour démarrer
        </p>
      )}
      {startError && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800 text-center">{startError}</p>
        </div>
      )}
    </div>
  );
}
