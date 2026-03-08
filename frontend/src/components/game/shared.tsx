import { useEffect, useRef, useState, useCallback } from 'react';
import { soundEffects } from '../../services/soundEffects';
import { getEffectiveMusicVolume } from './VolumeControl';
import type { GameRound } from '@/types';

/* ───────────────────── Types ───────────────────── */

interface RoundResults {
  correct_answer: string;
  points_earned?: number;
}

interface Props {
  round: GameRound;
  onAnswerSubmit: (answer: string) => void;
  hasAnswered: boolean;
  selectedAnswer: string | null;
  showResults: boolean;
  roundResults: RoundResults | null;
  seekOffsetMs?: number; // milliseconds to subtract from seek time (e.g. loading screen duration)
  excludedOptions?: string[]; // options to hide for 50/50 bonus
  fogBlur?: boolean; // brouillard : flouter les options pour les adversaires
}

/* ───────────────────── Shared audio hook ───────────────────── */
export function useAudioPlayer(
  round: GameRound,
  showResults: boolean,
  maxAudioDuration?: number,
  seekOffsetMs: number = 0,
  playbackRate: number = 1,
) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [needsPlay, setNeedsPlay] = useState(false);
  const [playerError, setPlayerError] = useState<string | null>(null);
  const mountedRef = useRef(true);
  const stopTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Set to true once the timer intentionally stops the audio — prevents fallback from restarting it
  const stoppedByTimerRef = useRef(false);

  const scheduleStop = useCallback((audioEl: HTMLAudioElement | null) => {
    if (stopTimeoutRef.current) {
      clearTimeout(stopTimeoutRef.current);
      stopTimeoutRef.current = null;
    }
    if (maxAudioDuration && maxAudioDuration < 30 && audioEl) {
      stopTimeoutRef.current = setTimeout(() => {
        if (audioRef.current) {
          audioRef.current.pause();
          stoppedByTimerRef.current = true;
          if (mountedRef.current) setIsPlaying(false);
        }
      }, maxAudioDuration * 1000);
    }
  }, [maxAudioDuration]);

  const getSeekTime = useCallback(() => {
    if (!round.started_at) return 0;
    return Math.max(0, (Date.now() - new Date(round.started_at).getTime() - seekOffsetMs) / 1000);
  }, [round.started_at, seekOffsetMs]);

  useEffect(() => {
    setIsPlaying(false);
    setNeedsPlay(false);
    setPlayerError(null);
    mountedRef.current = true;
    stoppedByTimerRef.current = false;

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
    audio.volume = getEffectiveMusicVolume();
    audio.playbackRate = playbackRate;
    audio.src = previewUrl;
    audioRef.current = audio;

    const onCanPlay = () => {
      if (!mountedRef.current) return;
      const seekTime = getSeekTime();
      if (seekTime > 0 && seekTime < 30) {
        try { audio.currentTime = seekTime; } catch (_) { /* ignore */ }
      }
      // Re-apply playbackRate right before play() — some browsers reset it after src load
      audio.playbackRate = playbackRate;
      audio.play()
        .then(() => {
          if (mountedRef.current) {
            audio.playbackRate = playbackRate; // force after play() resolves
            setIsPlaying(true);
            setNeedsPlay(false);
          }
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
    scheduleStop(audioRef.current);

    return () => {
      mountedRef.current = false;
      if (stopTimeoutRef.current) { clearTimeout(stopTimeoutRef.current); stopTimeoutRef.current = null; }
      audio.removeEventListener('canplaythrough', onCanPlay);
      audio.removeEventListener('error', onError);
      audio.removeEventListener('ended', onEnded);
      audio.pause();
      audio.removeAttribute('src');
      audio.load();
      audioRef.current = null;
    };
  }, [round.track_id, round.id, showResults, round.preview_url, getSeekTime, scheduleStop, playbackRate]);

  // Fallback: if playback didn't start after a short delay, mark as needing a manual play.
  // Do NOT trigger if the audio was intentionally stopped by the duration timer.
  useEffect(() => {
    if (showResults) return;
    const fallback = setTimeout(() => {
      if (!isPlaying && !playerError && !stoppedByTimerRef.current && mountedRef.current) setNeedsPlay(true);
    }, 3000);
    return () => clearTimeout(fallback);
  }, [isPlaying, playerError, showResults, round.track_id, round.id, round.preview_url]);

  const handlePlay = () => {
    // Do not restart audio if it was stopped intentionally by the duration timer
    if (stoppedByTimerRef.current) return;
    setPlayerError(null);
    if (audioRef.current) {
      audioRef.current.volume = getEffectiveMusicVolume();
      audioRef.current.playbackRate = playbackRate;
      const seekTime = getSeekTime();
      if (seekTime > 0 && seekTime < 30) {
        try { audioRef.current.currentTime = seekTime; } catch (_) { /* */ }
      }
      audioRef.current.play()
        .then(() => {
          if (audioRef.current) audioRef.current.playbackRate = playbackRate;
          setIsPlaying(true); setNeedsPlay(false);
        })
        .catch(() => setPlayerError('Impossible de lancer la lecture'));
      return;
    }
    const previewUrl = round.preview_url;
    if (!previewUrl) { setPlayerError('Aucun aperçu audio disponible'); return; }
    const audio = new Audio();
    audio.preload = 'auto';
    audio.volume = getEffectiveMusicVolume();
    audio.playbackRate = playbackRate;
    audio.src = previewUrl;
    audioRef.current = audio;
    const seekTime = getSeekTime();
    audio.addEventListener('canplaythrough', () => {
      if (seekTime > 0 && seekTime < 30) {
        try { audio.currentTime = seekTime; } catch (_) { /* */ }
      }
      audio.playbackRate = playbackRate;
      audio.play()
        .then(() => {
          audio.playbackRate = playbackRate;
          setIsPlaying(true); setNeedsPlay(false); scheduleStop(audioRef.current);
        })
        .catch(() => setPlayerError('Impossible de lancer la lecture'));
    }, { once: true });
    audio.addEventListener('error', () => setPlayerError("Impossible de charger l'aperçu audio"), { once: true });
    audio.addEventListener('ended', () => { if (stopTimeoutRef.current) { clearTimeout(stopTimeoutRef.current); stopTimeoutRef.current = null; } setIsPlaying(false); }, { once: true });
  };

  // Live volume sync: update currently-playing audio when slider changes
  useEffect(() => {
    const onVolumeChange = () => {
      if (audioRef.current) audioRef.current.volume = getEffectiveMusicVolume();
    };
    window.addEventListener('music-volume-change', onVolumeChange);
    return () => window.removeEventListener('music-volume-change', onVolumeChange);
  }, []);

  return { isPlaying, needsPlay, playerError, handlePlay };
}

/* ───────────────────── Audio hook for Lyrics mode (plays only on results) ───────────────────── */
export function useAudioPlayerOnResults(
  round: GameRound,
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
    audio.volume = getEffectiveMusicVolume();
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

    return () => {
      mountedRef.current = false;
      audio.removeEventListener('canplaythrough', onCanPlay);
      audio.removeEventListener('error', onError);
      audio.removeEventListener('ended', onEnded);
      audio.pause();
      audio.removeAttribute('src');
      audio.load();
      audioRef.current = null;
    };
  }, [round.track_id, round.id, showResults, round.preview_url]);

  // Fallback: if playback didn't start after a short delay, mark as needing a manual play
  useEffect(() => {
    if (!showResults) return;
    const fallback = setTimeout(() => {
      if (!isPlaying && !playerError && mountedRef.current) setNeedsPlay(true);
    }, 3000);
    return () => clearTimeout(fallback);
  }, [isPlaying, playerError, showResults, round.track_id, round.id, round.preview_url]);

  const handlePlay = () => {
    setPlayerError(null);
    if (audioRef.current) {
      audioRef.current.volume = getEffectiveMusicVolume();
      audioRef.current.play()
        .then(() => { setIsPlaying(true); setNeedsPlay(false); })
        .catch(() => setPlayerError('Impossible de lancer la lecture'));
      return;
    }
    const previewUrl = round.preview_url;
    if (!previewUrl) { setPlayerError('Aucun aperçu audio disponible'); return; }
    const audio = new Audio();
    audio.preload = 'auto';
    audio.volume = getEffectiveMusicVolume();
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
      if (audioRef.current) audioRef.current.volume = getEffectiveMusicVolume();
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
  hideManualPlay = false,
}: {
  isPlaying: boolean;
  needsPlay: boolean;
  playerError: string | null;
  handlePlay: () => void;
  label?: string;
  hideManualPlay?: boolean;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-2 md:p-4 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg min-h-[60px] md:min-h-[80px]">
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
            {needsPlay
              ? (hideManualPlay ? 'Cliquez n\u2019importe où pour lancer la musique' : 'Cliquez pour lancer la musique')
              : 'Chargement...'}
          </p>
          {needsPlay && !hideManualPlay && (
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
  excludedOptions = [],
  fogBlur = false,
}: {
  options: string[];
  hasAnswered: boolean;
  showResults: boolean;
  selectedAnswer: string | null;
  roundResults: RoundResults | null;
  onOptionClick: (option: string) => void;
  excludedOptions?: string[];
  fogBlur?: boolean;
}) {
  const visibleOptions = showResults
    ? options
    : options.filter((o) => !excludedOptions.includes(o));

  const getStyle = (option: string) => {
    if (!hasAnswered && !showResults)
      return 'bg-white hover:bg-blue-100 border-2 border-gray-300 hover:border-blue-500 cursor-pointer';
    if (hasAnswered && !showResults) {
      if (option === selectedAnswer) return 'bg-blue-500 text-white border-2 border-blue-700';
      return 'bg-gray-200 border-2 border-gray-300 cursor-not-allowed';
    }
    if (showResults && roundResults) {
      if (option === roundResults.correct_answer) return 'bg-green-500 text-white border-2 border-green-700 ring-4 ring-green-300 scale-[1.02]';
      if (option === selectedAnswer) return 'bg-red-500 text-white border-2 border-red-700';
      return 'bg-gray-200 border-2 border-gray-300';
    }
    return 'bg-white border-2 border-gray-300';
  };

  // Appliquer le brouillard tant que le joueur n’a pas répondu et que les résultats ne sont pas affichés
  const isBlurred = fogBlur && !hasAnswered && !showResults;

  return (
    <div
      className={`grid grid-cols-2 gap-3 md:gap-4 mb-4 md:mb-6 flex-1 transition-[filter] duration-1000${
        isBlurred ? ' blur-sm select-none' : ''
      }`}
    >
      {visibleOptions.map((option, index) => (
        <button
          key={index}
          onClick={() => { if (!hasAnswered && !showResults) { soundEffects.click(); onOptionClick(option); } }}
          className={`p-3 md:p-4 rounded-xl text-left transition-all duration-300 min-h-0 h-full overflow-hidden ${getStyle(option)}`}
          disabled={hasAnswered || showResults}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 shrink-0 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold text-sm">
              {String.fromCharCode(65 + index)}
            </div>
            <span className="text-base md:text-lg font-medium leading-tight line-clamp-2">{option}</span>
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
        <div className="text-center text-sm text-gray-600 animate-pulse mt-2 shrink-0">
          En attente des autres joueurs...
        </div>
      )}
      {showResults && roundResults && (
        <div className="mt-3 p-3 rounded-lg bg-blue-50 border-2 border-blue-200 shrink-0">
          <p className="text-base">
            <span className="font-bold">Bonne réponse :</span> {roundResults.correct_answer}
          </p>
          {selectedAnswer === roundResults.correct_answer ? (
            <p className="text-green-600 font-bold mt-1">
              ✓ Bravo ! +{roundResults.points_earned || 0} points
            </p>
          ) : (
            <p className="text-red-600 font-bold mt-1">
              ✗ Dommage ! C&apos;était &quot;{roundResults.correct_answer}&quot;
            </p>
          )}
        </div>
      )}
    </>
  );
}

/* ───────────────────── Track info (results phase) ───────────────────── */
export function TrackReveal({ round }: { round: GameRound }) {
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

export type { GameRound as Round, RoundResults, Props };
