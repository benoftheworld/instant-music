import { useEffect, useLayoutEffect, useRef, useState, useCallback } from 'react';
import { getEffectiveMusicVolume } from './VolumeControl';
import type { GameRound } from './types';

/* ───────────────────── Core (private) ───────────────────── */

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
    if (!startedAt || (!seekOffsetMs && seekOffsetMs !== 0)) return 0;
    return Math.max(0, (Date.now() - new Date(startedAt).getTime() - seekOffsetMs) / 1000);
  }, [seekOffsetMs]);

  const applySeek = useCallback((audio: HTMLAudioElement, startedAt?: string) => {
    const seekTime = getSeekTime(startedAt);
    if (seekTime > 0 && seekTime < 30) {
      try { audio.currentTime = seekTime; } catch { /* ignore */ }
    }
  }, [getSeekTime]);

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
    audio.addEventListener('ended', () => {
      if (stopTimeoutRef.current) { clearTimeout(stopTimeoutRef.current); stopTimeoutRef.current = null; }
      setIsPlaying(false);
    }, { once: true });
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

/* ───────────────────── Public hooks ───────────────────── */

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
  useLayoutEffect(() => {
    startedAtRef.current = round.started_at;
  }, [startedAtRef, round.started_at]);
  return result;
}

export function useAudioPlayerOnResults(
  round: GameRound,
  showResults: boolean,
) {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { startedAtRef: _, ...result } = useAudioPlayerCore(
    round.preview_url,
    showResults,
    [round.track_id, round.id, showResults, round.preview_url],
  );
  return result;
}
