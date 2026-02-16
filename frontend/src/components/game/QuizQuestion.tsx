import { useEffect, useRef, useState, useCallback } from 'react';

/* ───────────────────── YouTube IFrame API loader ───────────────────── */
declare global {
  interface Window { YT: any; onYouTubeIframeAPIReady: () => void }
}

let ytApiLoaded = false;
let ytApiReady = false;
const ytReadyCallbacks: (() => void)[] = [];

function ensureYTApi(): void {
  if (ytApiLoaded) return;
  ytApiLoaded = true;
  if (window.YT?.Player) { ytApiReady = true; return; }
  const tag = document.createElement('script');
  tag.src = 'https://www.youtube.com/iframe_api';
  document.head.appendChild(tag);
  const prev = window.onYouTubeIframeAPIReady;
  window.onYouTubeIframeAPIReady = () => {
    ytApiReady = true;
    prev?.();
    ytReadyCallbacks.forEach(cb => cb());
    ytReadyCallbacks.length = 0;
  };
}

function onYTReady(cb: () => void) {
  if (ytApiReady && window.YT?.Player) cb();
  else { ytReadyCallbacks.push(cb); ensureYTApi(); }
}

/* ───────────────────── Types ───────────────────── */
interface Round {
  id: string;
  round_number: number;
  track_id: string;
  track_name: string;
  artist_name: string;
  options: string[];
  duration: number;
  started_at: string;
  ended_at: string | null;
}

interface RoundResults {
  correct_answer: string;
  points_earned?: number;
}

interface QuizQuestionProps {
  round: Round;
  onAnswerSubmit: (answer: string) => void;
  hasAnswered: boolean;
  selectedAnswer: string | null;
  showResults: boolean;
  roundResults: RoundResults | null;
}

/* ───────────────────── Component ───────────────────── */
const QuizQuestion = ({
  round,
  onAnswerSubmit,
  hasAnswered,
  selectedAnswer,
  showResults,
  roundResults,
}: QuizQuestionProps) => {
  const playerRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [needsPlay, setNeedsPlay] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playerError, setPlayerError] = useState<string | null>(null);
  const mountedRef = useRef(true);
  // Track whether we already got a PLAYING state to avoid reacting to transient UNSTARTED
  const hasPlayedOnceRef = useRef(false);

  const getSeekTime = useCallback(() => {
    if (!round.started_at) return 0;
    return Math.max(0, Math.floor((Date.now() - new Date(round.started_at).getTime()) / 1000));
  }, [round.started_at]);

  /* ── Build a fresh YT.Player ── */
  const createPlayer = useCallback((divId: string, userGesture = false) => {
    const seekTime = getSeekTime();
    return new window.YT.Player(divId, {
      width: '320',
      height: '180',
      videoId: round.track_id,
      playerVars: {
        autoplay: userGesture ? 1 : 1,
        controls: 0,
        disablekb: 1,
        fs: 0,
        modestbranding: 1,
        rel: 0,
        start: seekTime,
        playsinline: 1,
        origin: window.location.origin,
      },
      events: {
        onReady: (e: any) => {
          if (!mountedRef.current) return;
          playerRef.current = e.target;
          e.target.setVolume(100);
          e.target.unMute();
          e.target.seekTo(getSeekTime(), true);
          e.target.playVideo();
        },
        onStateChange: (e: any) => {
          if (!mountedRef.current) return;
          const st = e.data;
          if (st === window.YT.PlayerState.PLAYING) {
            hasPlayedOnceRef.current = true;
            setIsPlaying(true);
            setNeedsPlay(false);
            setPlayerError(null);
          } else if (st === window.YT.PlayerState.PAUSED && hasPlayedOnceRef.current) {
            // Browser paused it (visibility change, etc.)
            setNeedsPlay(true);
            setIsPlaying(false);
          }
          // Ignore UNSTARTED / CUED — these are transient states before autoplay kicks in
        },
        onError: (e: any) => {
          if (!mountedRef.current) return;
          const code = e.data;
          const msgs: Record<number, string> = {
            2: 'ID vidéo invalide',
            5: 'Erreur HTML5 player',
            100: 'Vidéo introuvable ou supprimée',
            101: 'Lecture intégrée non autorisée',
            150: 'Lecture intégrée non autorisée',
          };
          setPlayerError(msgs[code] || `Erreur YouTube (${code})`);
          setNeedsPlay(false);
          setIsPlaying(false);
        },
      },
    });
  }, [round.track_id, getSeekTime]);

  /* ── Main effect: create player on new round / destroy on results ── */
  useEffect(() => {
    // Reset state for new round
    setIsPlaying(false);
    setNeedsPlay(false);
    setPlayerError(null);
    hasPlayedOnceRef.current = false;

    if (showResults) {
      if (playerRef.current) {
        try { playerRef.current.destroy(); } catch (_) { /* */ }
        playerRef.current = null;
      }
      return;
    }

    mountedRef.current = true;
    let ytPlayer: any = null;

    onYTReady(() => {
      if (!mountedRef.current || !containerRef.current) return;

      // Destroy previous player
      if (playerRef.current) {
        try { playerRef.current.destroy(); } catch (_) { /* */ }
        playerRef.current = null;
      }

      // Fresh div
      containerRef.current.innerHTML = '';
      const div = document.createElement('div');
      div.id = `yt-${round.id}-${Date.now()}`;
      containerRef.current.appendChild(div);

      ytPlayer = createPlayer(div.id);
    });

    // Fallback: show play button after 3s if not playing
    const fallback = setTimeout(() => {
      if (!isPlaying && !playerError && mountedRef.current) {
        setNeedsPlay(true);
      }
    }, 3000);

    return () => {
      mountedRef.current = false;
      clearTimeout(fallback);
      if (ytPlayer?.destroy) {
        try { ytPlayer.destroy(); } catch (_) { /* */ }
      }
      playerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [round.track_id, round.id, showResults]);

  /* ── Manual play button (user gesture → no autoplay restriction) ── */
  const handlePlay = () => {
    setPlayerError(null);

    // If player exists, just try playing
    if (playerRef.current) {
      try {
        playerRef.current.setVolume(100);
        playerRef.current.unMute();
        playerRef.current.seekTo(getSeekTime(), true);
        playerRef.current.playVideo();
        return;
      } catch (_) { /* recreate below */ }
    }

    // Recreate player (user gesture context)
    if (containerRef.current && window.YT?.Player) {
      containerRef.current.innerHTML = '';
      const div = document.createElement('div');
      div.id = `yt-retry-${round.id}-${Date.now()}`;
      containerRef.current.appendChild(div);
      createPlayer(div.id, true);
    }
  };

  /* ── Option helpers ── */
  const handleOptionClick = (option: string) => {
    if (!hasAnswered && !showResults) onAnswerSubmit(option);
  };

  const getOptionStyle = (option: string) => {
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

  /* ───────────────────── Render ───────────────────── */
  return (
    <div className="bg-white rounded-lg shadow-xl p-8">
      {/* Question header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Quel est le titre de ce morceau ?
        </h2>
        <p className="text-gray-600">
          Artiste : <span className="font-semibold">{round.artist_name}</span>
        </p>
      </div>

      {/* ── Audio player (quiz phase) ── */}
      {!showResults && (
        <div className="mb-6">
          <div className="flex flex-col items-center justify-center p-6 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg min-h-[120px]">
            {playerError ? (
              <div className="text-white text-center">
                <div className="text-4xl mb-2">⚠️</div>
                <p className="text-sm mb-1">{playerError}</p>
                <p className="text-xs opacity-70 mb-3">Vidéo : {round.track_id}</p>
                <button
                  onClick={handlePlay}
                  className="px-6 py-2 bg-white text-purple-600 rounded-lg hover:bg-gray-100 transition font-bold shadow"
                >
                  🔄 Réessayer
                </button>
              </div>
            ) : isPlaying ? (
              <div className="text-white text-center">
                <div className="text-4xl mb-2 animate-pulse">🎵</div>
                <p className="text-sm">Écoutez attentivement...</p>
              </div>
            ) : (
              <div className="text-white text-center">
                <div className="text-4xl mb-2">{needsPlay ? '🔇' : '⏳'}</div>
                <p className="text-sm mb-3">
                  {needsPlay ? 'Cliquez pour lancer la musique' : 'Chargement...'}
                </p>
                {needsPlay && (
                  <button
                    onClick={handlePlay}
                    className="px-8 py-4 bg-white text-purple-600 rounded-xl hover:bg-gray-100 transition font-bold text-lg shadow-lg"
                  >
                    ▶️ Lancer la musique
                  </button>
                )}
              </div>
            )}
          </div>
          {/* Off-screen container for YT player (audio only) */}
          <div
            ref={containerRef}
            style={{
              position: 'fixed',
              left: '-9999px',
              top: 0,
              width: '320px',
              height: '180px',
              overflow: 'hidden',
              opacity: 0,
              pointerEvents: 'none',
            }}
          />
        </div>
      )}

      {/* ── Video player (results phase) ── */}
      {showResults && (
        <div className="mb-6 rounded-lg overflow-hidden shadow-lg">
          <iframe
            width="100%"
            height="315"
            src={`https://www.youtube.com/embed/${round.track_id}?autoplay=0&controls=1&modestbranding=1&rel=0`}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="w-full"
          />
        </div>
      )}

      {/* ── Answer options ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {round.options.map((option, index) => (
          <button
            key={index}
            onClick={() => handleOptionClick(option)}
            className={`p-4 rounded-lg text-left transition-all duration-200 ${getOptionStyle(option)}`}
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

      {/* Status message */}
      {hasAnswered && !showResults && (
        <div className="text-center text-lg text-gray-600 animate-pulse">
          En attente des autres joueurs...
        </div>
      )}

      {/* Results */}
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
    </div>
  );
};

export default QuizQuestion;