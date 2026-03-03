import { useEffect, useRef, useState } from 'react';
import { getEffectiveMusicVolume } from './VolumeControl';
import { getMediaUrl } from '@/services/api';

interface Round {
  id: string;
  round_number: number;
  track_id: string;
  track_name: string;
  artist_name: string;
  preview_url?: string;
  options: string[];
  question_type: string;
  question_text: string;
  extra_data: Record<string, any>;
  duration: number;
  started_at: string;
  ended_at: string | null;
}

interface Player {
  id: string;
  username: string;
  score: number;
  avatar?: string;
}

/** Per-player score data for the current round (from backend round_ended event) */
interface PlayerRoundScore {
  points_earned: number;
  is_correct: boolean;
  response_time: number;
  streak_bonus?: number;
  consecutive_correct?: number;
}

interface RoundResultsScreenProps {
  round: Round;
  players: Player[];
  correctAnswer: string;
  myPointsEarned: number;
  /** The answer the current player submitted (null if no answer) */
  myAnswer?: string | null;
  /** Per-player round scores keyed by username */
  playerScores?: Record<string, PlayerRoundScore>;
  onContinue?: () => void;
}

/**
 * Hook to auto-play the track preview on the results screen.
 */
function useResultsAudio(previewUrl?: string) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [needsPlay, setNeedsPlay] = useState(false);

  useEffect(() => {
    setIsPlaying(false);
    setNeedsPlay(false);

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.removeAttribute('src');
      audioRef.current.load();
      audioRef.current = null;
    }

    if (!previewUrl) return;

    const audio = new Audio();
    audio.preload = 'auto';
    audio.volume = getEffectiveMusicVolume();
    audio.src = previewUrl;
    audioRef.current = audio;

    const onCanPlay = () => {
      audio.play()
        .then(() => { setIsPlaying(true); setNeedsPlay(false); })
        .catch(() => setNeedsPlay(true));
    };
    const onEnded = () => setIsPlaying(false);

    audio.addEventListener('canplaythrough', onCanPlay, { once: true });
    audio.addEventListener('ended', onEnded);

    const fallback = setTimeout(() => {
      if (!audioRef.current) return;
      setNeedsPlay(true);
    }, 3000);

    return () => {
      clearTimeout(fallback);
      audio.removeEventListener('canplaythrough', onCanPlay);
      audio.removeEventListener('ended', onEnded);
      audio.pause();
      audio.removeAttribute('src');
      audio.load();
      audioRef.current = null;
    };
  }, [previewUrl]);

  const handlePlay = () => {
    if (audioRef.current) {
      audioRef.current.play()
        .then(() => { setIsPlaying(true); setNeedsPlay(false); })
        .catch(() => {});
    }
  };

  // Live volume sync
  useEffect(() => {
    const onVolumeChange = () => {
      if (audioRef.current) audioRef.current.volume = getEffectiveMusicVolume();
    };
    window.addEventListener('music-volume-change', onVolumeChange);
    return () => window.removeEventListener('music-volume-change', onVolumeChange);
  }, []);

  return { isPlaying, needsPlay, handlePlay };
}

export default function RoundResultsScreen({
  round,
  players,
  correctAnswer,
  myPointsEarned,
  myAnswer,
  playerScores,
  onContinue,
}: RoundResultsScreenProps) {
  const audio = useResultsAudio(round.preview_url);

  // Sort players by score and take top 5
  const topPlayers = [...players]
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);

  // Extract year from extra_data if available
  const year = round.extra_data?.year || round.extra_data?.release_date?.substring(0, 4) || null;
  const albumImage = round.extra_data?.album_image;

  /** Format a player answer that may be JSON (legacy) or plain text for display. */
  const formatAnswer = (answer: string): string => {
    try {
      const parsed = JSON.parse(answer);
      if (parsed && typeof parsed === 'object') {
        const parts: string[] = [];
        if (parsed.artist) parts.push(parsed.artist);
        if (parsed.title) parts.push(parsed.title);
        if (parts.length) return parts.join(' - ');
      }
    } catch { /* not JSON, use as-is */ }
    return answer;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4 flex items-center justify-center">
      <div className="container mx-auto max-w-5xl">
        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-green-500 to-teal-500 p-6 text-center">
            <div className="text-5xl mb-3">🎉</div>
            <h2 className="text-3xl font-bold text-white mb-2">
              Fin du Round {round.round_number}
            </h2>
            <p className="text-white/90 text-lg">
              {myPointsEarned > 0 ? `+${myPointsEarned} points !` : 'Aucun point'}
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 p-6">
            {/* Left: Track Info */}
            <div className="space-y-4">
              <h3 className="text-xl font-bold text-gray-800 mb-4">
                🎵 Informations sur la musique
              </h3>

              {/* Album Art */}
              {albumImage ? (
                <div className="rounded-lg overflow-hidden shadow-lg">
                  <img
                    src={albumImage}
                    alt={`${round.track_name} album art`}
                    className="w-full h-auto object-cover"
                    onError={(e) => {
                      // Fallback if image doesn't load
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                </div>
              ) : (
                <div className="bg-gradient-to-br from-purple-400 to-blue-500 rounded-lg shadow-lg h-64 flex items-center justify-center">
                  <div className="text-white text-6xl">🎶</div>
                </div>
              )}

              {/* Audio Player */}
              <div className="flex items-center justify-center p-4 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg">
                {audio.isPlaying ? (
                  <div className="text-white text-center">
                    <div className="text-3xl animate-pulse">🎵</div>
                    <p className="text-sm mt-1">Lecture en cours...</p>
                  </div>
                ) : audio.needsPlay ? (
                  <button
                    onClick={audio.handlePlay}
                    className="px-6 py-3 bg-white text-purple-600 rounded-lg hover:bg-gray-100 transition font-bold shadow"
                  >
                    ▶️ Écouter
                  </button>
                ) : (
                  <div className="text-white text-center">
                    <div className="text-3xl">⏳</div>
                    <p className="text-sm mt-1">Chargement...</p>
                  </div>
                )}
              </div>

              {/* Track Details */}
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div>
                  <p className="text-sm text-gray-500 font-medium">Titre</p>
                  <p className="text-lg font-bold text-gray-900">{round.track_name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 font-medium">Artiste</p>
                  <p className="text-lg font-bold text-gray-900">{round.artist_name}</p>
                </div>
                {year && (
                  <div>
                    <p className="text-sm text-gray-500 font-medium">Année</p>
                    <p className="text-lg font-bold text-gray-900">{year}</p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-gray-500 font-medium">Bonne réponse</p>
                  <p className="text-lg font-bold text-green-600">{correctAnswer}</p>
                </div>
                {myAnswer !== undefined && myAnswer !== null && (
                  <div>
                    <p className="text-sm text-gray-500 font-medium">Votre réponse</p>
                    <p className={`text-lg font-bold ${
                      myPointsEarned > 0 ? 'text-green-600' : 'text-red-500'
                    }`}>
                      {formatAnswer(myAnswer)} {myPointsEarned > 0 ? '✓' : '✗'}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Right: Top 5 Players */}
            <div className="space-y-4">
              <h3 className="text-xl font-bold text-gray-800 mb-4">
                🏆 Top 5 Joueurs
              </h3>

              <div className="space-y-3">
                {topPlayers.map((player, index) => (
                  <div
                    key={player.id}
                    className={`flex items-center gap-4 rounded-lg p-4 transition-all ${
                      index === 0
                        ? 'bg-gradient-to-r from-yellow-400 to-yellow-500 shadow-lg scale-105'
                        : index === 1
                        ? 'bg-gradient-to-r from-gray-300 to-gray-400 shadow-md'
                        : index === 2
                        ? 'bg-gradient-to-r from-orange-400 to-orange-500 shadow-md'
                        : 'bg-gray-100'
                    }`}
                  >
                    {/* Rank */}
                    <div
                      className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${
                        index < 3 ? 'text-white' : 'text-gray-700 bg-white'
                      }`}
                    >
                      {index + 1}
                    </div>

                    {/* Avatar */}
                    {player.avatar ? (
                      <img
                        src={getMediaUrl(player.avatar) ?? player.avatar}
                        alt={player.username}
                        className="w-12 h-12 rounded-full object-cover"
                        onError={(e) => { e.currentTarget.style.display = 'none'; }}
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-blue-500 flex items-center justify-center text-white font-bold">
                        {player.username.charAt(0).toUpperCase()}
                      </div>
                    )}

                    {/* Player Info */}
                    <div className="flex-1">
                      <p
                        className={`font-bold ${
                          index < 3 ? 'text-white' : 'text-gray-900'
                        }`}
                      >
                        {player.username}
                      </p>
                      <p
                        className={`text-sm ${
                          index < 3 ? 'text-white/80' : 'text-gray-500'
                        }`}
                      >
                        {player.score} points
                      </p>
                      {/* Per-round details */}
                      {playerScores?.[player.username] && (
                        <div className={`flex flex-col gap-0.5 mt-0.5 text-xs ${
                          index < 3 ? 'text-white/70' : 'text-gray-400'
                        }`}>
                          <div className="flex items-center gap-2">
                            <span className={playerScores[player.username].is_correct
                              ? (index < 3 ? 'text-green-200' : 'text-green-500')
                              : (index < 3 ? 'text-red-200' : 'text-red-400')
                            }>
                              {playerScores[player.username].is_correct ? '✓' : '✗'}
                              {' '}+{playerScores[player.username].points_earned} pts
                            </span>
                            <span>•</span>
                            <span>
                              ⏱ {playerScores[player.username].response_time.toFixed(1)}s
                            </span>
                          </div>
                          {(playerScores[player.username].streak_bonus ?? 0) > 0 && (
                            <span className={index < 3 ? 'text-orange-200' : 'text-orange-400'}>
                              🔥 Série ×{playerScores[player.username].consecutive_correct} +{playerScores[player.username].streak_bonus} pts
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Medal for top 3 */}
                    {index === 0 && <div className="text-2xl">🥇</div>}
                    {index === 1 && <div className="text-2xl">🥈</div>}
                    {index === 2 && <div className="text-2xl">🥉</div>}
                  </div>
                ))}
              </div>

              {/* Continue Button */}
              {onContinue && (
                <button
                  onClick={onContinue}
                  className="w-full mt-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all shadow-lg"
                >
                  Continuer
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Auto-continue message */}
        <p className="text-center text-white/70 mt-4 text-sm">
          Le prochain round commencera automatiquement...
        </p>
      </div>
    </div>
  );
}
