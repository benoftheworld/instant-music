import { useEffect, useRef, useState, useCallback } from 'react';
import type { Props } from './shared';

/* ═══════════════════════════════════════════════════════════════════ */
/*                     YouTube IFrame Player hook                    */
/* ═══════════════════════════════════════════════════════════════════ */

/** Ensure the YT IFrame API script is loaded exactly once. */
let ytApiLoading = false;
let ytApiReady = false;
const ytReadyCallbacks: (() => void)[] = [];

function loadYouTubeApi(): Promise<void> {
  return new Promise((resolve) => {
    if (ytApiReady && (window as any).YT?.Player) {
      resolve();
      return;
    }
    ytReadyCallbacks.push(resolve);
    if (ytApiLoading) return;
    ytApiLoading = true;

    const prev = (window as any).onYouTubeIframeAPIReady;
    (window as any).onYouTubeIframeAPIReady = () => {
      ytApiReady = true;
      if (prev) prev();
      ytReadyCallbacks.forEach((cb) => cb());
      ytReadyCallbacks.length = 0;
    };

    if (!document.getElementById('yt-iframe-api')) {
      const tag = document.createElement('script');
      tag.id = 'yt-iframe-api';
      tag.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(tag);
    }
  });
}

interface UseYouTubePlayerResult {
  containerRef: React.RefObject<HTMLDivElement>;
  isReady: boolean;
  isPlaying: boolean;
  currentTimeMs: number;
  error: string | null;
  play: () => void;
  pause: () => void;
}

/**
 * Embeds a YouTube player in the given container div and exposes
 * playback state + `currentTimeMs` polled every ~80 ms for lyric sync.
 */
function useYouTubePlayer(
  videoId: string | undefined,
  active: boolean,
): UseYouTubePlayerResult {
  const containerRef = useRef<HTMLDivElement>(null!);
  const playerRef = useRef<any>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [isReady, setIsReady] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTimeMs, setCurrentTimeMs] = useState(0);
  const [error, setError] = useState<string | null>(null);

  /* Start polling getCurrentTime when playing */
  const startPoll = useCallback(() => {
    if (pollRef.current) return;
    pollRef.current = setInterval(() => {
      if (playerRef.current?.getCurrentTime) {
        setCurrentTimeMs(playerRef.current.getCurrentTime() * 1000);
      }
    }, 80);
  }, []);

  const stopPoll = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  /* Initialise or re-create the player when videoId changes */
  useEffect(() => {
    if (!videoId || !active) return;
    let destroyed = false;

    const init = async () => {
      try {
        await loadYouTubeApi();
      } catch {
        setError('Impossible de charger le lecteur YouTube');
        return;
      }
      if (destroyed || !containerRef.current) return;

      // Clear any existing player
      if (playerRef.current?.destroy) {
        try { playerRef.current.destroy(); } catch { /* noop */ }
        playerRef.current = null;
      }

      // Create a fresh div inside the container for the player
      const hostDiv = document.createElement('div');
      hostDiv.id = `yt-player-${videoId}`;
      containerRef.current.innerHTML = '';
      containerRef.current.appendChild(hostDiv);

      const YT = (window as any).YT;
      playerRef.current = new YT.Player(hostDiv.id, {
        videoId,
        width: '100%',
        height: '100%',
        playerVars: {
          autoplay: 1,
          controls: 1,
          modestbranding: 1,
          rel: 0,
          fs: 0,
          playsinline: 1,
        },
        events: {
          onReady: () => {
            if (destroyed) return;
            setIsReady(true);
            setError(null);
            try { playerRef.current.playVideo(); } catch { /* noop */ }
          },
          onStateChange: (event: any) => {
            if (destroyed) return;
            const state = event.data;
            // YT.PlayerState: PLAYING=1, PAUSED=2, ENDED=0, BUFFERING=3
            if (state === 1) {
              setIsPlaying(true);
              startPoll();
            } else {
              setIsPlaying(false);
              if (state !== 3) stopPoll(); // keep polling while buffering
            }
          },
          onError: () => {
            if (destroyed) return;
            setError('Impossible de lire cette vidéo YouTube');
          },
        },
      });
    };

    init();

    return () => {
      destroyed = true;
      stopPoll();
      if (playerRef.current?.destroy) {
        try { playerRef.current.destroy(); } catch { /* noop */ }
        playerRef.current = null;
      }
      setIsReady(false);
      setIsPlaying(false);
      setCurrentTimeMs(0);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [videoId, active]);

  const play = useCallback(() => {
    playerRef.current?.playVideo?.();
  }, []);

  const pause = useCallback(() => {
    playerRef.current?.pauseVideo?.();
  }, []);

  return { containerRef: containerRef as React.RefObject<HTMLDivElement>, isReady, isPlaying, currentTimeMs, error, play, pause };
}

/* ═══════════════════════════════════════════════════════════════════ */
/*                   Synced-lyrics display components                */
/* ═══════════════════════════════════════════════════════════════════ */

interface SyncedLine {
  time_ms: number;
  text: string;
}

/** Find the active lyric line index from current playback position. */
function useActiveLyricIndex(lines: SyncedLine[], currentTimeMs: number): number {
  const [activeIndex, setActiveIndex] = useState(-1);

  useEffect(() => {
    if (lines.length === 0) {
      setActiveIndex(-1);
      return;
    }
    let idx = -1;
    for (let i = lines.length - 1; i >= 0; i--) {
      if (currentTimeMs >= lines[i].time_ms) {
        idx = i;
        break;
      }
    }
    setActiveIndex(idx);
  }, [lines, currentTimeMs]);

  return activeIndex;
}

function KaraokeLyricsDisplay({
  lines,
  activeIndex,
}: {
  lines: SyncedLine[];
  activeIndex: number;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef<HTMLParagraphElement>(null);

  // Keep a fixed visible area equal to 4 lines and position active line
  // so that 2 previous lines + current + 1 next are visible.
  useEffect(() => {
    const container = containerRef.current;
    const active = activeRef.current;
    if (!container || !active) return;

    // Determine a sensible line height: prefer the active element height,
    // fallback to the first paragraph inside the container.
    const firstLine = container.querySelector<HTMLParagraphElement>('p');
    const lineHeight = (active.clientHeight || firstLine?.clientHeight || 32);

    // Ensure container has height for 4 lines
    const visibleLines = 4;
    container.style.height = `${lineHeight * visibleLines}px`;

    // Compute scroll position so active line sits after 2 previous lines
    const target = Math.max(0, active.offsetTop - lineHeight * 2);
    container.scrollTo({ top: target, behavior: 'smooth' });
  }, [activeIndex, lines]);

  if (lines.length === 0) return null;

  return (
    <>
      <style>{`[data-hide-scroll] { -ms-overflow-style: none; scrollbar-width: none; } [data-hide-scroll]::-webkit-scrollbar { display: none; }`}</style>
      <div
        data-hide-scroll
        ref={containerRef}
        className="relative flex-1 min-h-0 overflow-hidden overflow-y-auto scrollbar-hide rounded-2xl bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950"
      >
      {/* Gradient masks */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-16 bg-gradient-to-b from-gray-950 to-transparent z-10" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-gray-950 to-transparent z-10" />

      <div className="space-y-6 py-8 px-6">
        {lines.map((line, i) => {
          const isCurrent = i === activeIndex;
          const isPast = i < activeIndex;
          const isEmpty = !line.text;

          if (isEmpty) return <div key={i} className="h-6" />;

          return (
            <p
              key={i}
              ref={isCurrent ? activeRef : undefined}
              className={`text-center transition-all duration-500 leading-relaxed ${
                isCurrent
                  ? 'text-yellow-300 text-6xl md:text-7xl font-extrabold scale-105 drop-shadow-lg'
                  : isPast
                    ? 'text-gray-600 text-2xl md:text-3xl'
                    : 'text-gray-400 text-4xl md:text-5xl'
              }`}
            >
              {line.text}
            </p>
          );
        })}
      </div>
    </div>
    </>
  );
}

/* ═══════════════════════════════════════════════════════════════════ */
/*                 Score sidebar (placeholder for voice rec)         */
/* ═══════════════════════════════════════════════════════════════════ */

function KaraokeScoreSidebar({ score }: { score: number }) {
  return (
    <div className="flex flex-col items-center gap-4">
      <div className="bg-gray-900/80 backdrop-blur border border-gray-700 rounded-2xl p-6 text-center min-w-[140px]">
        <div className="text-gray-400 text-xs uppercase tracking-wider mb-1">Score</div>
        <div className="text-4xl font-black text-yellow-400">{score}</div>
        <div className="text-gray-500 text-xs mt-1">pts</div>
      </div>

      <div className="bg-gray-900/60 border border-gray-700/50 rounded-xl p-4 text-center">
        <div className="text-2xl mb-1">🎤</div>
        <p className="text-gray-500 text-xs leading-tight max-w-[120px]">
          Reconnaissance vocale bientôt disponible !
        </p>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════ */
/*                        KaraokeQuestion                            */
/* ═══════════════════════════════════════════════════════════════════ */

interface KaraokeProps extends Props {
  onSkipSong?: () => void;
}

const KaraokeQuestion = ({
  round,
  showResults,
  onSkipSong,
}: KaraokeProps) => {
  const syncedLines: SyncedLine[] = round.extra_data?.synced_lyrics ?? [];
  const youtubeVideoId: string | undefined = round.extra_data?.youtube_video_id;

  const yt = useYouTubePlayer(youtubeVideoId, !showResults);
  const activeIndex = useActiveLyricIndex(syncedLines, yt.currentTimeMs);

  /* ── Results phase: show track info ── */
  if (showResults) {
    return (
      <div className="bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 rounded-2xl shadow-2xl p-8 text-center">
        <div className="text-5xl mb-4">🎶</div>
        <p className="text-2xl font-bold text-white mb-1">{round.track_name}</p>
        <p className="text-lg text-gray-400">{round.artist_name}</p>
      </div>
    );
  }

  /* ── Playing phase: YouTube + lyrics + score ── */
  return (
    <div className="bg-gradient-to-br from-gray-900 via-purple-950 to-gray-900 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
      {/* Top bar: video + track info + score */}
      <div className="flex items-start gap-4 p-4">
        {/* YouTube player (visible, min 200×200 per ToS) */}
        <div className="flex-shrink-0">
          <div
            ref={yt.containerRef}
            className="rounded-xl overflow-hidden bg-black"
            style={{ width: '240px', height: '200px' }}
          />
          {yt.error && (
            <p className="text-red-400 text-xs mt-2 text-center max-w-[240px]">{yt.error}</p>
          )}
          {!yt.isReady && !yt.error && (
            <p className="text-gray-500 text-xs mt-2 text-center animate-pulse">Chargement YouTube…</p>
          )}
        </div>

        {/* Track info */}
        <div className="flex-1 min-w-0 pt-2">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl">🎤</span>
            <h2 className="text-xl font-bold text-white truncate">{round.track_name}</h2>
          </div>
          <p className="text-gray-400 text-sm truncate">{round.artist_name}</p>

          {yt.isPlaying && (
            <div className="mt-3 flex items-center gap-2">
              <div className="flex gap-[3px]">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className="w-1 bg-yellow-400 rounded-full animate-pulse"
                    style={{
                      height: `${12 + Math.random() * 12}px`,
                      animationDelay: `${i * 120}ms`,
                    }}
                  />
                ))}
              </div>
              <span className="text-yellow-400 text-xs font-medium">En cours…</span>
            </div>
          )}
        </div>

        {/* Score sidebar */}
        <KaraokeScoreSidebar score={0} />
      </div>

      {/* Lyrics area (flexes to remaining space without growing past viewport) */}
      <div className="px-4 pb-4 flex-1 min-h-0">
        <KaraokeLyricsDisplay lines={syncedLines} activeIndex={activeIndex} />
      </div>

      {/* Skip button */}
      {onSkipSong && (
        <div className="px-4 pb-4 text-center">
          <button
            onClick={onSkipSong}
            className="px-6 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white rounded-xl transition-all text-sm font-medium border border-gray-700"
          >
            ⏭️ Chanson suivante
          </button>
        </div>
      )}
    </div>
  );
};

export default KaraokeQuestion;
