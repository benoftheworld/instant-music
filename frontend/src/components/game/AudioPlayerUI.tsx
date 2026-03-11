export function AudioPlayerUI({
  isPlaying,
  needsPlay,
  playerError,
  handlePlay,
  label,
  hideManualPlay = false,
  compact = false,
}: {
  isPlaying: boolean;
  needsPlay: boolean;
  playerError: string | null;
  handlePlay: () => void;
  label?: string;
  hideManualPlay?: boolean;
  compact?: boolean;
}) {
  if (compact) {
    return (
      <div className="shrink-0">
        {playerError ? (
          <button
            onClick={handlePlay}
            className="text-xs bg-red-100 text-red-600 px-2 py-1 rounded-lg"
          >
            ⚠️ Réessayer
          </button>
        ) : needsPlay ? (
          <button
            onClick={handlePlay}
            className="flex items-center gap-1 px-3 py-2 bg-primary-500 text-white rounded-lg text-sm font-bold shadow"
          >
            ▶️ Écouter
          </button>
        ) : isPlaying ? (
          <span className="flex items-center gap-1 text-xs font-medium text-white">
            <span className="animate-pulse">🎵</span> En écoute
          </span>
        ) : (
          <span className="text-xs text-gray-400">Chargement…</span>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center p-2 md:p-4 bg-gradient-to-r from-primary-600 to-primary-400 rounded-lg min-h-[60px] md:min-h-[80px]">
      {playerError ? (
        <div className="text-white text-center">
          <div className="text-4xl mb-2">⚠️</div>
          <p className="text-sm mb-1">{playerError}</p>
          <button
            onClick={handlePlay}
            className="mt-3 px-6 py-2 bg-white text-primary-600 rounded-lg hover:bg-cream-100 transition font-bold shadow"
          >
            🔄 Réessayer
          </button>
        </div>
      ) : isPlaying ? (
        <div className="text-white text-center">
          <div className="text-4xl mb-2 animate-pulse">🎵</div>
          <p className="text-sm">{label || 'Écoutez attentivement...'}</p>
        </div>
      ) : (
        <div className="text-white text-center">
          <div className="text-4xl mb-2">{needsPlay ? '🔇' : '⏳'}</div>
          <p className="text-sm mb-3">
            {needsPlay
              ? hideManualPlay
                ? 'Cliquez n\u2019importe où pour lancer la musique'
                : 'Cliquez pour lancer la musique'
              : 'Chargement...'}
          </p>
          {needsPlay && !hideManualPlay && (
            <button
              onClick={handlePlay}
              className="px-8 py-4 bg-white text-primary-600 rounded-xl hover:bg-cream-100 transition font-bold text-lg shadow-lg"
            >
              ▶️ Lancer la musique
            </button>
          )}
        </div>
      )}
    </div>
  );
}
