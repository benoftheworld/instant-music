import type { GameMode, AnswerMode, GuessTarget, YouTubePlaylist, KaraokeSong } from '../../../types';
import { gameModes } from './gameModes';

interface Props {
  isKaraoke: boolean;
  isOnline: boolean;
  isPublic: boolean;
  isPartyMode: boolean;
  isBonusesEnabled: boolean;
  selectedMode: GameMode;
  answerMode: AnswerMode;
  guessTarget: GuessTarget;
  lyricsWordsCount: number;
  roundDuration: number;
  scoreDisplayDuration: number;
  maxPlayers: number;
  numRounds: number;
  selectedPlaylist: YouTubePlaylist | null;
  karaokeSelectedSong: KaraokeSong | null;
}

export default function StepConfirm({
  isKaraoke,
  isOnline,
  isPublic,
  isPartyMode,
  isBonusesEnabled,
  selectedMode,
  answerMode,
  guessTarget,
  lyricsWordsCount,
  roundDuration,
  scoreDisplayDuration,
  maxPlayers,
  numRounds,
  selectedPlaylist,
  karaokeSelectedSong,
}: Props) {
  const modeConfig = gameModes.find((m) => m.value === selectedMode);

  return (
    <div className="card space-y-6">
      <h3 className="text-lg font-bold bg-[#C42F38] text-white text-center py-2 px-3 rounded">Récapitulatif</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Global config summary */}
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold text-sm text-gray-500 uppercase mb-3">Configuration</h4>
          <ul className="space-y-2 text-sm">
            <li><span className="text-gray-500">⏳ Timer début :</span> <strong>5s</strong></li>
            {!isKaraoke && (
              <>
                <li><span className="text-gray-500">Durée round :</span> <strong>{roundDuration}s</strong></li>
                <li><span className="text-gray-500">Rounds :</span> <strong>{numRounds}</strong></li>
                <li><span className="text-gray-500">Joueurs max :</span> <strong>{maxPlayers}</strong></li>
                <li><span className="text-gray-500">Score affichage :</span> <strong>{scoreDisplayDuration}s</strong></li>
                <li><span className="text-gray-500">Mode :</span> <strong>{isOnline ? 'En ligne' : 'Hors ligne'}</strong></li>
                {isOnline && (
                  <li><span className="text-gray-500">Visibilité :</span> <strong>{isPublic ? '🌐 Publique' : '🔒 Privée'}</strong></li>
                )}
                {isOnline && isPartyMode && (
                  <li><span className="text-gray-500">Mode Soirée :</span> <strong>🎉 Activé</strong></li>
                )}
                {isOnline && (
                  <li><span className="text-gray-500">Bonus :</span> <strong>{isBonusesEnabled ? '⚡ Activés' : '🚫 Désactivés'}</strong></li>
                )}
              </>
            )}
            {isKaraoke && (
              <>
                <li><span className="text-gray-500">Round :</span> <strong>1 (durée auto)</strong></li>
                <li><span className="text-gray-500">Mode :</span> <strong>Hors ligne / solo</strong></li>
              </>
            )}
          </ul>
        </div>

        {/* Mode summary */}
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold text-sm text-gray-500 uppercase mb-3">Mode de jeu</h4>
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">{modeConfig?.icon}</span>
            <div>
              <p className="font-bold">{modeConfig?.label}</p>
              <p className="text-xs text-gray-600">{modeConfig?.description}</p>
            </div>
          </div>
          {!isKaraoke && (
            <ul className="space-y-2 text-sm">
              <li>
                <span className="text-gray-500">Réponse :</span>{' '}
                <strong>{answerMode === 'mcq' ? 'QCM' : 'Saisie libre'}</strong>
              </li>
              {(selectedMode === 'classique' || selectedMode === 'rapide' || selectedMode === 'mollo') && answerMode === 'mcq' && (
                <li>
                  <span className="text-gray-500">Cible :</span>{' '}
                  <strong>{guessTarget === 'artist' ? 'Artiste' : 'Titre'}</strong>
                </li>
              )}
              {selectedMode === 'paroles' && (
                <li>
                  <span className="text-gray-500">Mots à trouver :</span>{' '}
                  <strong>{lyricsWordsCount}</strong>
                </li>
              )}
            </ul>
          )}
        </div>
      </div>

      {/* Karaoke song summary */}
      {isKaraoke && karaokeSelectedSong && (
        <div className="p-4 bg-pink-50 border border-pink-200 rounded-lg">
          <h4 className="font-semibold text-sm text-pink-600 uppercase mb-3">🎤 Morceau karaoké</h4>
          <div className="flex items-center gap-4">
            {karaokeSelectedSong.album_image_url && (
              <img
                src={karaokeSelectedSong.album_image_url}
                alt={karaokeSelectedSong.title}
                className="w-16 h-16 rounded-md object-cover"
              />
            )}
            <div>
              <p className="font-bold">{karaokeSelectedSong.title}</p>
              <p className="text-sm text-gray-600">{karaokeSelectedSong.artist}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-gray-400">{karaokeSelectedSong.duration_display}</span>
                {karaokeSelectedSong.lrclib_id ? (
                  <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full">
                    ✓ Paroles synchronisées
                  </span>
                ) : (
                  <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">
                    ⚠ Recherche auto paroles
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Playlist summary (non-karaoke) */}
      {!isKaraoke && selectedPlaylist && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold text-sm text-gray-500 uppercase mb-3">Playlist</h4>
          <div className="flex items-center gap-4">
            {selectedPlaylist.image_url && (
              <img
                src={selectedPlaylist.image_url}
                alt={selectedPlaylist.name}
                className="w-16 h-16 rounded-md object-cover"
              />
            )}
            <div>
              <p className="font-bold">{selectedPlaylist.name}</p>
              <p className="text-sm text-gray-600">
                {selectedPlaylist.total_tracks} morceaux • {selectedPlaylist.owner}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
