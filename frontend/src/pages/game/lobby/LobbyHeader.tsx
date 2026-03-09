import { Game } from '../../../types';

interface LobbyHeaderProps {
  game: Game;
  isConnected: boolean;
  copyMessage: string | null;
  onCopyRoomCode: () => void;
  onShareGame: () => void;
}

export default function LobbyHeader({
  game,
  isConnected,
  copyMessage,
  onCopyRoomCode,
  onShareGame,
}: LobbyHeaderProps) {
  return (
    <div className="card mb-6">
      {/* Title + connexion status */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <h1 className="text-2xl md:text-3xl font-bold leading-tight">
          {game.name || 'Lobby de jeu'}
        </h1>
        <div className={`shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
          isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
          {isConnected ? 'Connecté' : 'Déconnecté'}
        </div>
      </div>

      {/* Info badges */}
      <div className="flex flex-wrap gap-2 mb-4">
        <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-100 text-primary-700 rounded-full text-xs font-semibold">
          🎮 {game.mode}
        </span>
        <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-100 text-primary-700 rounded-full text-xs font-semibold">
          🔄 {game.num_rounds} rounds
        </span>
        <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-100 text-primary-700 rounded-full text-xs font-semibold">
          ⏱ {game.round_duration || 30}s / round
        </span>
        {game.answer_mode === 'text' ? (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-100 text-primary-700 rounded-full text-xs font-semibold">
            ⌨️ Saisie libre
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-100 text-primary-700 rounded-full text-xs font-semibold">
            📋 QCM
          </span>
        )}
        {(game.mode === 'classique' || game.mode === 'rapide') && game.answer_mode === 'mcq' && (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-100 text-primary-700 rounded-full text-xs font-semibold">
            {game.guess_target === 'artist' ? '🎤 Artiste' : '🎵 Titre'}
          </span>
        )}
        {game.is_party_mode && (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-100 text-primary-700 rounded-full text-xs font-semibold">
            🎉 Mode Soirée
          </span>
        )}
      </div>

      {/* Room code + share */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-gray-500 shrink-0">Code de salle :</span>
        <code className="text-xl md:text-2xl font-bold text-primary-600 bg-primary-50 px-3 py-1 rounded-lg tracking-wider">
          {game.room_code}
        </code>
        <button
          onClick={onCopyRoomCode}
          className="p-2 hover:bg-gray-100 rounded-md transition-colors"
          title="Copier le code"
        >
          <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
        <button
          onClick={onShareGame}
          className="p-2 bg-primary-100 hover:bg-primary-200 rounded-md transition-colors text-primary-600"
          title="Partager le lien"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
          </svg>
        </button>
        {copyMessage && (
          <span className="text-sm text-green-600 font-medium animate-pulse">
            ✓ {copyMessage}
          </span>
        )}
      </div>
    </div>
  );
}
