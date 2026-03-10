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

/* ───────────────────── Core audio hook (shared logic) ───────────────────── */

interface AudioCoreOptions {
  playbackRate?: number;
  seekOffsetMs?: number;
  maxAudioDuration?: number;
}

function useAudioPlayerCore(
  previewUrl: string | undefined,
  shouldPlay: boolean,
  deps: unknown[],
  options: AudioCoreOptions = {},
) {
  const { playbackRate = 1, seekOffsetMs = 0, maxAudioDuration } = options;
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [needsPlay, setNeedsPlay] = useState(false);
  const [playerError, setPlayerError] = useState<string | null>(null);
  const mountedRef = useRef(true);
  const stopTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
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

  const getSeekTime = useCallback((startedAt?: string) => {
    if (!startedAt || !seekOffsetMs && seekOffsetMs !== 0) return 0;
    return Math.max(0, (Date.now() - new Date(startedAt).getTime() - seekOffsetMs) / 1000);
  }, [seekOffsetMs]);

  const applySeek = useCallback((audio: HTMLAudioElement, startedAt?: string) => {
    const seekTime = getSeekTime(startedAt);
    if (seekTime > 0 && seekTime < 30) {
      try { audio.currentTime = seekTime; } catch (_) { /* ignore */ }
    }
  }, [getSeekTime]);

  // startedAt ref for use in callbacks — kept in sync via deps
  const startedAtRef = useRef<string | undefined>();

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

    if (!shouldPlay) return;

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
      applySeek(audio, startedAtRef.current);
      audio.playbackRate = playbackRate;
      audio.play()
        .then(() => {
          if (mountedRef.current) {
            audio.playbackRate = playbackRate;
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  // Fallback: if playback didn't start after a short delay, mark as needing a manual play.
  useEffect(() => {
    if (!shouldPlay) return;
    const fallback = setTimeout(() => {
      if (!isPlaying && !playerError && !stoppedByTimerRef.current && mountedRef.current) setNeedsPlay(true);
    }, 3000);
    return () => clearTimeout(fallback);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isPlaying, playerError, shouldPlay, ...deps]);

  const handlePlay = useCallback(() => {
    if (stoppedByTimerRef.current) return;
    setPlayerError(null);
    if (audioRef.current) {
      audioRef.current.volume = getEffectiveMusicVolume();
      audioRef.current.playbackRate = playbackRate;
      applySeek(audioRef.current, startedAtRef.current);
      audioRef.current.play()
        .then(() => {
          if (audioRef.current) audioRef.current.playbackRate = playbackRate;
          setIsPlaying(true); setNeedsPlay(false);
        })
        .catch(() => setPlayerError('Impossible de lancer la lecture'));
      return;
    }
    if (!previewUrl) { setPlayerError('Aucun aperçu audio disponible'); return; }
    const audio = new Audio();
    audio.preload = 'auto';
    audio.volume = getEffectiveMusicVolume();
    audio.playbackRate = playbackRate;
    audio.src = previewUrl;
    audioRef.current = audio;
    audio.addEventListener('canplaythrough', () => {
      applySeek(audio, startedAtRef.current);
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
  }, [previewUrl, playbackRate, applySeek, scheduleStop]);

  // Live volume sync
  useEffect(() => {
    const onVolumeChange = () => {
      if (audioRef.current) audioRef.current.volume = getEffectiveMusicVolume();
    };
    window.addEventListener('music-volume-change', onVolumeChange);
    return () => window.removeEventListener('music-volume-change', onVolumeChange);
  }, []);

  return { isPlaying, needsPlay, playerError, handlePlay, startedAtRef };
}

/* ───────────────────── Public audio hooks ───────────────────── */

export function useAudioPlayer(
  round: GameRound,
  showResults: boolean,
  maxAudioDuration?: number,
  seekOffsetMs: number = 0,
  playbackRate: number = 1,
) {
  const { startedAtRef, ...result } = useAudioPlayerCore(
    round.preview_url,
    !showResults,
    [round.track_id, round.id, showResults, round.preview_url, seekOffsetMs, playbackRate],
    { playbackRate, seekOffsetMs, maxAudioDuration },
  );
  startedAtRef.current = round.started_at;
  return result;
}

export function useAudioPlayerOnResults(
  round: GameRound,
  showResults: boolean,
) {
  const { startedAtRef: _, ...result } = useAudioPlayerCore(
    round.preview_url,
    showResults,
    [round.track_id, round.id, showResults, round.preview_url],
  );
  return result;
}

/* ───────────────────── Shared AudioPlayer UI ───────────────────── */
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
          <span className="flex items-center gap-1 text-xs text-white-600 font-medium">
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
          <button onClick={handlePlay}
            className="mt-3 px-6 py-2 bg-white text-primary-600 rounded-lg hover:bg-cream-100 transition font-bold shadow">
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
              className="px-8 py-4 bg-white text-primary-600 rounded-xl hover:bg-cream-100 transition font-bold text-lg shadow-lg">
              ▶️ Lancer la musique
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/* ───────────────────── Shared Question Header ───────────────────── */
export function QuestionHeader({
  title,
  subtitle,
  badge,
  audioStatus,
}: {
  icon: string;
  title: string;
  subtitle?: string;
  badge?: React.ReactNode;
  audioStatus?: React.ReactNode;
  gradientFrom?: string;
  gradientTo?: string;
}) {
  return (
    <div className="bg-gradient-to-r from-primary-600 to-primary-500 rounded-t-2xl px-6 py-3 flex items-center justify-between shrink-0 mb-4 md:mb-6">
      <div className="flex items-center gap-3">
        <div>
          <h2 className="text-xl font-bold text-white">
            {title}
          </h2>
          <p className="text-gray-400 text-xs mt-0.5 truncate">{subtitle}</p>
        </div>
        {badge}
      </div>
      <div className="flex items-center gap-2">
        {audioStatus}
      </div>
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
      return 'bg-white hover:bg-primary-100 border-2 border-cream-300 hover:border-primary-500 cursor-pointer';
    if (hasAnswered && !showResults) {
      if (option === selectedAnswer) return 'bg-primary-500 text-white border-2 border-primary-700';
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
      className={`grid grid-cols-1 sm:grid-cols-2 gap-2 md:gap-3 mb-4 md:mb-6 transition-[filter] duration-1000${
        isBlurred ? ' blur-sm select-none' : ''
      }`}
    >
      {visibleOptions.map((option, index) => (
        <button
          key={index}
          onClick={() => { if (!hasAnswered && !showResults) { soundEffects.click(); onOptionClick(option); } }}
          className={`p-3 md:p-5 rounded-xl text-left transition-all duration-300 ${getStyle(option)}`}
          disabled={hasAnswered || showResults}
        >
          <div className="flex items-center gap-2 md:gap-3">
            <div className="w-7 h-7 md:w-8 md:h-8 shrink-0 rounded-full bg-primary-500 text-white flex items-center justify-center font-bold text-xs md:text-sm">
              {String.fromCharCode(65 + index)}
            </div>
            <span className="text-sm md:text-lg font-medium leading-tight break-words">{option}</span>
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
        <div className="mt-3 p-3 rounded-lg bg-primary-50 border-2 border-primary-200 shrink-0">
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

export type { GameRound as Round, RoundResults, Props };
