import type { GameMode } from '../../../types';

interface Props {
  selectedMode: GameMode;
  isKaraoke: boolean;
  isOnline: boolean;
  isPublic: boolean;
  setIsPublic: (v: boolean) => void;
  isPartyMode: boolean;
  setIsPartyMode: React.Dispatch<React.SetStateAction<boolean>>;
  isBonusesEnabled: boolean;
  setIsBonusesEnabled: React.Dispatch<React.SetStateAction<boolean>>;
  roundDuration: number;
  setRoundDuration: (v: number) => void;
  scoreDisplayDuration: number;
  setScoreDisplayDuration: (v: number) => void;
  lyricsWordsCount: number;
  setLyricsWordsCount: (v: number) => void;
  maxPlayers: number;
  setMaxPlayers: (v: number) => void;
  numRounds: number;
  setNumRounds: (v: number) => void;
  handleToggleOffline: (checked: boolean) => void;
}

export default function StepConfig({
  selectedMode,
  isKaraoke,
  isOnline,
  isPublic,
  setIsPublic,
  isPartyMode,
  setIsPartyMode,
  isBonusesEnabled,
  setIsBonusesEnabled,
  roundDuration,
  setRoundDuration,
  scoreDisplayDuration,
  setScoreDisplayDuration,
  lyricsWordsCount,
  setLyricsWordsCount,
  maxPlayers,
  setMaxPlayers,
  numRounds,
  setNumRounds,
  handleToggleOffline,
}: Props) {
  return (
    <div className="card">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left column */}
        <div className="space-y-6">
          {!isKaraoke && (
            <>
              <div className="flex flex-col gap-2 w-full">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  🎵 Temps du round
                </label>
                <div className="flex gap-4 w-full justify-center">
                  <input
                    type="range"
                    min="10"
                    max="30"
                    step="5"
                    value={roundDuration}
                    onChange={(e) => setRoundDuration(parseInt(e.target.value))}
                    className="w-48 md:w-full"
                  />
                  <span className="text-lg font-semibold text-primary-600 min-w-[4rem]">
                    {roundDuration}s
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  Durée pour répondre à chaque question
                </p>
              </div>

              <div className="flex flex-col gap-2 w-full">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  🏆 Temps affichage score fin de round
                </label>
                <div className="flex gap-4 w-full justify-center">
                  <input
                    type="range"
                    min="10"
                    max="30"
                    value={scoreDisplayDuration}
                    onChange={(e) => setScoreDisplayDuration(parseInt(e.target.value))}
                    className="w-48 md:w-full"
                  />
                  <span className="text-lg font-semibold text-primary-600 min-w-[4rem]">
                    {scoreDisplayDuration}s
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  Durée d'affichage des résultats après chaque round
                </p>
              </div>

              {selectedMode === 'paroles' && (
                <div className="flex flex-col items-center gap-2 w-full">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nombre de mots à trouver
                  </label>
                  <div className="flex items-center gap-4 w-full justify-center">
                    <input
                      type="range"
                      min="2"
                      max="10"
                      value={lyricsWordsCount}
                      onChange={(e) => setLyricsWordsCount(parseInt(e.target.value))}
                      className="w-48 md:w-full"
                    />
                    <span className="text-lg font-semibold text-primary-600 min-w-[4rem]">
                      {lyricsWordsCount} mot{lyricsWordsCount > 1 ? 's' : ''}
                    </span>
                  </div>
                  <div className="flex w-full justify-between text-xs text-gray-500 px-2">
                    <span>2</span>
                    <span>10</span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">Nombre de mots masqués dans les paroles</p>
                </div>
              )}
            </>
          )}
          {isOnline && (
            <div className="flex gap-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <input
                type="checkbox"
                id="isPublic"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                className="w-5 h-5 text-green-600 border-gray-300 rounded focus:ring-green-500"
              />
              <div>
                <label htmlFor="isPublic" className="text-sm font-medium text-gray-700">
                  🌐 Partie publique
                </label>
                <p className="text-xs text-gray-500 mt-1">
                  Visible dans la liste des parties publiques. N'importe qui peut rejoindre.
                </p>
              </div>
            </div>
          )}
          {isOnline && (
            <div
              className={`flex gap-4 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                isPartyMode
                  ? 'bg-primary-50 border-primary-400'
                  : 'bg-gray-50 border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setIsPartyMode((v) => !v)}
            >
              <input
                type="checkbox"
                id="isPartyMode"
                checked={isPartyMode}
                onChange={(e) => setIsPartyMode(e.target.checked)}
                className="w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500 mt-0.5 shrink-0"
                onClick={(e) => e.stopPropagation()}
              />
              <div>
                <label htmlFor="isPartyMode" className="text-sm font-medium text-gray-700 cursor-pointer">
                  🎉 Mode Soirée
                </label>
                <p className="text-xs text-gray-500 mt-1">
                  L'hôte projette l'interface complète sur grand écran. Les joueurs voient
                  uniquement les boutons de réponse sur leur téléphone.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {!isKaraoke && (
            <>
              {isOnline && (
                <div className="flex flex-col gap-2 w-full">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    👥 Nombre maximum de joueurs
                  </label>
                  <div className="flex gap-4 w-full justify-center">
                    <input
                      type="range"
                      min="2"
                      max="20"
                      value={maxPlayers}
                      onChange={(e) => setMaxPlayers(parseInt(e.target.value))}
                      className="w-48 md:w-full"
                    />
                    <span className="text-lg font-semibold text-primary-600 min-w-[3rem]">
                      {maxPlayers}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">Nombre maximum de joueurs</p>
                </div>
              )}

              <div className="flex flex-col gap-2 w-full">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  🔄 Nombre de rounds
                </label>
                <div className="flex gap-4 w-full justify-center">
                  <input
                    type="range"
                    min="3"
                    max="20"
                    value={numRounds}
                    onChange={(e) => setNumRounds(parseInt(e.target.value))}
                    className="w-48 md:w-full"
                  />
                  <span className="text-lg font-semibold text-primary-600 min-w-[3rem]">
                    {numRounds}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">Nombre de rounds à jouer</p>
              </div>

              <div className="flex gap-4 p-4 bg-gray-50 rounded-lg">
                <input
                  type="checkbox"
                  id="isOffline"
                  checked={!isOnline}
                  onChange={(e) => handleToggleOffline(e.target.checked)}
                  className="w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <div>
                  <label htmlFor="isOffline" className="text-sm font-medium text-gray-700">
                    📴 Mode hors ligne (solo)
                  </label>
                  <p className="text-xs text-gray-500 mt-1">Joueur unique. Bonus désactivés.</p>
                </div>
              </div>
            </>
          )}
          {isOnline && (
            <div
              className={`flex gap-4 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                !isBonusesEnabled
                  ? 'bg-orange-50 border-orange-400'
                  : 'bg-gray-50 border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setIsBonusesEnabled((v) => !v)}
            >
              <input
                type="checkbox"
                id="isBonusesEnabled"
                checked={isBonusesEnabled}
                onChange={(e) => setIsBonusesEnabled(e.target.checked)}
                className="w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500 mt-0.5 shrink-0"
                onClick={(e) => e.stopPropagation()}
              />
              <div>
                <label htmlFor="isBonusesEnabled" className="text-sm font-medium text-gray-700 cursor-pointer">
                  ⚡ Bonus activés
                </label>
                <p className="text-xs text-gray-500 mt-1">
                  Décochez pour interdire l'utilisation des bonus durant cette partie.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
