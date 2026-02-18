import { useEffect, useRef, useState, useCallback } from 'react';
import { soundEffects } from '../../services/soundEffects';
import { getGlobalMusicVolume } from './VolumeControl';

/* ───────────────────── Types ───────────────────── */
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
  correct_answer?: string;
}

interface RoundResults {
  correct_answer: string;
  points_earned?: number;
}

interface Props {
  round: Round;
  onAnswerSubmit: (answer: string) => void;
  hasAnswered: boolean;
  selectedAnswer: string | null;
  showResults: boolean;
  roundResults: RoundResults | null;
  seekOffsetMs?: number; // milliseconds to subtract from seek time (e.g. loading screen duration)
}

/* ───────────────────── Shared audio hook ───────────────────── */
export function useAudioPlayer(
  round: Round,
  showResults: boolean,
  maxAudioDuration?: number,
  seekOffsetMs: number = 0,
) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [needsPlay, setNeedsPlay] = useState(false);
  const [playerError, setPlayerError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const getSeekTime = useCallback(() => {
    if (!round.started_at) return 0;
    return Math.max(0, (Date.now() - new Date(round.started_at).getTime() - seekOffsetMs) / 1000);
  }, [round.started_at, seekOffsetMs]);

  useEffect(() => {
    setIsPlaying(false);
    setNeedsPlay(false);
    setPlayerError(null);
    mountedRef.current = true;

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.removeAttribute('src');
      audioRef.current.load();
      audioRef.current = null;
    }

    if (showResults) return;

    const previewUrl = round.preview_url;
    if (!previewUrl) {
      setPlayerError('Aucun aperçu audio disponible pour ce morceau');
      return;
    }

    const audio = new Audio();
    audio.preload = 'auto';
    audio.volume = getGlobalMusicVolume();
    audio.src = previewUrl;
    audioRef.current = audio;

    const onCanPlay = () => {
      if (!mountedRef.current) return;
      const seekTime = getSeekTime();
      if (seekTime > 0 && seekTime < 30) {
        try { audio.currentTime = seekTime; } catch (_) { /* ignore */ }
      }
      audio.play()
        .then(() => {
          if (mountedRef.current) { setIsPlaying(true); setNeedsPlay(false); }
        })
        .catch(() => {
          if (mountedRef.current) setNeedsPlay(true);
        });
    };

    const onError = () => {
      if (!mountedRef.current) return;
      setPlayerError("Impossible de charger l'aperçu audio");
      setIsPlaying(false);
    };
    const onEnded = () => { if (mountedRef.current) setIsPlaying(false); };

    audio.addEventListener('canplaythrough', onCanPlay, { once: true });
    audio.addEventListener('error', onError);
    audio.addEventListener('ended', onEnded);

    // For intro mode: stop audio after maxAudioDuration seconds
    let stopTimeout: ReturnType<typeof setTimeout> | null = null;
    if (maxAudioDuration && maxAudioDuration < 30) {
      stopTimeout = setTimeout(() => {
        if (audioRef.current) {
          audioRef.current.pause();
          if (mountedRef.current) setIsPlaying(false);
        }
      }, maxAudioDuration * 1000);
    }

    const fallback = setTimeout(() => {
      if (!isPlaying && !playerError && mountedRef.current) setNeedsPlay(true);
    }, 3000);

    return () => {
      mountedRef.current = false;
      clearTimeout(fallback);
      if (stopTimeout) clearTimeout(stopTimeout);
      audio.removeEventListener('canplaythrough', onCanPlay);
      audio.removeEventListener('error', onError);
      audio.removeEventListener('ended', onEnded);
      audio.pause();
      audio.removeAttribute('src');
      audio.load();
      audioRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [round.track_id, round.id, showResults, round.preview_url]);

  const handlePlay = () => {
    setPlayerError(null);
    if (audioRef.current) {
      audioRef.current.volume = getGlobalMusicVolume();
      const seekTime = getSeekTime();
      if (seekTime > 0 && seekTime < 30) {
        try { audioRef.current.currentTime = seekTime; } catch (_) { /* */ }
      }
      audioRef.current.play()
        .then(() => { setIsPlaying(true); setNeedsPlay(false); })
        .catch(() => setPlayerError('Impossible de lancer la lecture'));
      return;
    }
    const previewUrl = round.preview_url;
    if (!previewUrl) { setPlayerError('Aucun aperçu audio disponible'); return; }
    const audio = new Audio();
    audio.preload = 'auto';
    audio.volume = getGlobalMusicVolume();
    audio.src = previewUrl;
    audioRef.current = audio;
    const seekTime = getSeekTime();
    audio.addEventListener('canplaythrough', () => {
      if (seekTime > 0 && seekTime < 30) {
        try { audio.currentTime = seekTime; } catch (_) { /* */ }
      }
      audio.play()
        .then(() => { setIsPlaying(true); setNeedsPlay(false); })
        .catch(() => setPlayerError('Impossible de lancer la lecture'));
    }, { once: true });
    audio.addEventListener('error', () => setPlayerError("Impossible de charger l'aperçu audio"), { once: true });
    audio.addEventListener('ended', () => setIsPlaying(false), { once: true });
  };

  // Live volume sync: update currently-playing audio when slider changes
  useEffect(() => {
    const onVolumeChange = () => {
      if (audioRef.current) audioRef.current.volume = getGlobalMusicVolume();
    };
    window.addEventListener('music-volume-change', onVolumeChange);
    return () => window.removeEventListener('music-volume-change', onVolumeChange);
  }, []);

  return { isPlaying, needsPlay, playerError, handlePlay };
}

/* ───────────────────── Audio hook for Lyrics mode (plays only on results) ───────────────────── */
export function useAudioPlayerOnResults(
  round: Round,
  showResults: boolean,
) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [needsPlay, setNeedsPlay] = useState(false);
  const [playerError, setPlayerError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    setIsPlaying(false);
    setNeedsPlay(false);
    setPlayerError(null);
    mountedRef.current = true;

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.removeAttribute('src');
      audioRef.current.load();
      audioRef.current = null;
    }

    // Only play audio when results are shown
    if (!showResults) return;

    const previewUrl = round.preview_url;
    if (!previewUrl) {
      setPlayerError('Aucun aperçu audio disponible pour ce morceau');
      return;
    }

    const audio = new Audio();
    audio.preload = 'auto';
    audio.volume = getGlobalMusicVolume();
    audio.src = previewUrl;
    audioRef.current = audio;

    const onCanPlay = () => {
      if (!mountedRef.current) return;
      audio.play()
        .then(() => {
          if (mountedRef.current) { setIsPlaying(true); setNeedsPlay(false); }
        })
        .catch(() => {
          if (mountedRef.current) setNeedsPlay(true);
        });
    };

    const onError = () => {
      if (!mountedRef.current) return;
      setPlayerError("Impossible de charger l'aperçu audio");
      setIsPlaying(false);
    };
    const onEnded = () => { if (mountedRef.current) setIsPlaying(false); };

    audio.addEventListener('canplaythrough', onCanPlay, { once: true });
    audio.addEventListener('error', onError);
    audio.addEventListener('ended', onEnded);

    const fallback = setTimeout(() => {
      if (!isPlaying && !playerError && mountedRef.current) setNeedsPlay(true);
    }, 3000);

    return () => {
      mountedRef.current = false;
      clearTimeout(fallback);
      audio.removeEventListener('canplaythrough', onCanPlay);
      audio.removeEventListener('error', onError);
      audio.removeEventListener('ended', onEnded);
      audio.pause();
      audio.removeAttribute('src');
      audio.load();
      audioRef.current = null;
    };
  }, [round.track_id, round.id, showResults, round.preview_url]);

  const handlePlay = () => {
    setPlayerError(null);
    if (audioRef.current) {
      audioRef.current.volume = getGlobalMusicVolume();
      audioRef.current.play()
        .then(() => { setIsPlaying(true); setNeedsPlay(false); })
        .catch(() => setPlayerError('Impossible de lancer la lecture'));
      return;
    }
    const previewUrl = round.preview_url;
    if (!previewUrl) { setPlayerError('Aucun aperçu audio disponible'); return; }
    const audio = new Audio();
    audio.preload = 'auto';
    audio.volume = getGlobalMusicVolume();
    audio.src = previewUrl;
    audioRef.current = audio;
    audio.addEventListener('canplaythrough', () => {
      audio.play()
        .then(() => { setIsPlaying(true); setNeedsPlay(false); })
        .catch(() => setPlayerError('Impossible de lancer la lecture'));
    }, { once: true });
    audio.addEventListener('error', () => setPlayerError("Impossible de charger l'aperçu audio"), { once: true });
    audio.addEventListener('ended', () => setIsPlaying(false), { once: true });
  };

  // Live volume sync: update audio element when slider changes
  useEffect(() => {
    const onVolumeChange = () => {
      if (audioRef.current) audioRef.current.volume = getGlobalMusicVolume();
    };
    window.addEventListener('music-volume-change', onVolumeChange);
    return () => window.removeEventListener('music-volume-change', onVolumeChange);
  }, []);

  return { isPlaying, needsPlay, playerError, handlePlay };
}

/* ───────────────────── Shared AudioPlayer UI ───────────────────── */
export function AudioPlayerUI({
  isPlaying,
  needsPlay,
  playerError,
  handlePlay,
  label,
}: {
  isPlaying: boolean;
  needsPlay: boolean;
  playerError: string | null;
  handlePlay: () => void;
  label?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-6 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg min-h-[120px]">
      {playerError ? (
        <div className="text-white text-center">
          <div className="text-4xl mb-2">⚠️</div>
          <p className="text-sm mb-1">{playerError}</p>
          <button onClick={handlePlay}
            className="mt-3 px-6 py-2 bg-white text-purple-600 rounded-lg hover:bg-gray-100 transition font-bold shadow">
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
            {needsPlay ? 'Cliquez pour lancer la musique' : 'Chargement...'}
          </p>
          {needsPlay && (
            <button onClick={handlePlay}
              className="px-8 py-4 bg-white text-purple-600 rounded-xl hover:bg-gray-100 transition font-bold text-lg shadow-lg">
              ▶️ Lancer la musique
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/* ───────────────────── Shared MCQ Options grid ───────────────────── */
export function OptionsGrid({
  options,
  hasAnswered,
  showResults,
  selectedAnswer,
  roundResults,
  onOptionClick,
}: {
  options: string[];
  hasAnswered: boolean;
  showResults: boolean;
  selectedAnswer: string | null;
  roundResults: RoundResults | null;
  onOptionClick: (option: string) => void;
}) {
  const getStyle = (option: string) => {
    if (!hasAnswered && !showResults)
      return 'bg-white hover:bg-blue-100 border-2 border-gray-300 hover:border-blue-500 cursor-pointer';
    if (hasAnswered && !showResults) {
      if (option === selectedAnswer) return 'bg-blue-500 text-white border-2 border-blue-700';
      return 'bg-gray-200 border-2 border-gray-300 cursor-not-allowed';
    }
    if (showResults && roundResults) {
      if (option === roundResults.correct_answer) return 'bg-green-500 text-white border-2 border-green-700';
      if (option === selectedAnswer) return 'bg-red-500 text-white border-2 border-red-700';
      return 'bg-gray-200 border-2 border-gray-300';
    }
    return 'bg-white border-2 border-gray-300';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
      {options.map((option, index) => (
        <button
          key={index}
          onClick={() => { if (!hasAnswered && !showResults) { soundEffects.click(); onOptionClick(option); } }}
          className={`p-4 rounded-lg text-left transition-all duration-200 ${getStyle(option)}`}
          disabled={hasAnswered || showResults}
        >
          <div className="flex items-center">
            <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center mr-3 font-bold">
              {String.fromCharCode(65 + index)}
            </div>
            <span className="text-lg font-medium">{option}</span>
          </div>
        </button>
      ))}
    </div>
  );
}

/* ───────────────────── Results footer ───────────────────── */
export function ResultFooter({
  showResults,
  roundResults,
  selectedAnswer,
  hasAnswered,
}: {
  showResults: boolean;
  roundResults: RoundResults | null;
  selectedAnswer: string | null;
  hasAnswered: boolean;
}) {
  return (
    <>
      {hasAnswered && !showResults && (
        <div className="text-center text-lg text-gray-600 animate-pulse">
          En attente des autres joueurs...
        </div>
      )}
      {showResults && roundResults && (
        <div className="mt-6 p-4 rounded-lg bg-blue-50 border-2 border-blue-200">
          <p className="text-lg">
            <span className="font-bold">Bonne réponse :</span> {roundResults.correct_answer}
          </p>
          {selectedAnswer === roundResults.correct_answer ? (
            <p className="text-green-600 font-bold mt-2">
              ✓ Bravo ! +{roundResults.points_earned || 0} points
            </p>
          ) : (
            <p className="text-red-600 font-bold mt-2">
              ✗ Dommage ! C&apos;était &quot;{roundResults.correct_answer}&quot;
            </p>
          )}
        </div>
      )}
    </>
  );
}

/* ───────────────────── Track info (results phase) ───────────────────── */
export function TrackReveal({ round }: { round: Round }) {
  return (
    <div className="mb-6 rounded-lg overflow-hidden shadow-lg bg-gradient-to-r from-purple-600 to-blue-600 p-6">
      <div className="text-white text-center">
        <div className="text-4xl mb-2">🎶</div>
        <p className="text-lg font-bold">{round.track_name}</p>
        <p className="text-sm opacity-80">{round.artist_name}</p>
      </div>
    </div>
  );
}

export type { Round, RoundResults, Props };
