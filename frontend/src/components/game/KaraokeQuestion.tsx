import { useEffect, useRef, useState, useCallback } from 'react';
import {
  useAudioPlayer, AudioPlayerUI, OptionsGrid, ResultFooter, TrackReveal,
  type Props, type Round,
} from './shared';

/* ───────────────── Synced-lyrics time-tracking hook ───────────────── */

interface SyncedLine {
  time_ms: number;
  text: string;
}

/**
 * Returns the index of the currently-active lyric line based on audio
 * playback progress.  Falls back to an elapsed-time estimate when no
 * `audioElement` is provided.
 */
function useLyricSync(
  lines: SyncedLine[],
  round: Round,
  showResults: boolean,
) {
  const [activeIndex, setActiveIndex] = useState(-1);
  const rafRef = useRef<number | null>(null);
  // Shared audio element reference — we rely on the one created by useAudioPlayer
  // but that hook doesn't expose its ref.  So we track elapsed time from round.started_at
  // which is reliable because the audio is synced to the same clock.

  const tick = useCallback(() => {
    if (showResults || !round.started_at || lines.length === 0) {
      setActiveIndex(-1);
      return;
    }
    const elapsedMs = Date.now() - new Date(round.started_at).getTime();
    let idx = -1;
    for (let i = lines.length - 1; i >= 0; i--) {
      if (elapsedMs >= lines[i].time_ms) {
        idx = i;
        break;
      }
    }
    setActiveIndex(idx);
    rafRef.current = requestAnimationFrame(tick);
  }, [lines, round.started_at, showResults]);

  useEffect(() => {
    if (showResults) {
      setActiveIndex(-1);
      return;
    }
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [tick, showResults]);

  return activeIndex;
}

/* ───────────────── Scrolling lyrics display ───────────────── */

function LyricsScroller({
  lines,
  activeIndex,
}: {
  lines: SyncedLine[];
  activeIndex: number;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef<HTMLParagraphElement>(null);

  // Auto-scroll so the active line stays centred
  useEffect(() => {
    if (activeRef.current && containerRef.current) {
      activeRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [activeIndex]);

  if (lines.length === 0) return null;

  return (
    <div
      ref={containerRef}
      className="relative mb-6 p-4 bg-gray-900 rounded-xl overflow-hidden max-h-64 overflow-y-auto scrollbar-hide"
    >
      {/* Gradient overlays for fade-in / fade-out effect */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-10 bg-gradient-to-b from-gray-900 to-transparent z-10" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-gray-900 to-transparent z-10" />

      <div className="space-y-2 py-6">
        {lines.map((line, i) => {
          const isCurrent = i === activeIndex;
          const isPast = i < activeIndex;
          const isEmpty = !line.text;

          if (isEmpty) {
            return <div key={i} className="h-4" />;
          }

          return (
            <p
              key={i}
              ref={isCurrent ? activeRef : undefined}
              className={`text-center transition-all duration-300 ${
                isCurrent
                  ? 'text-yellow-300 text-xl font-bold scale-105'
                  : isPast
                  ? 'text-gray-500 text-sm'
                  : 'text-gray-300 text-base'
              }`}
            >
              {line.text}
            </p>
          );
        })}
      </div>
    </div>
  );
}

/* ───────────────── Plain-lyrics fallback (no timestamps) ─────────── */

function PlainLyricsDisplay({ lines }: { lines: string[] }) {
  return (
    <div className="mb-6 p-4 bg-gray-900 rounded-xl max-h-64 overflow-y-auto scrollbar-hide">
      <div className="space-y-1 py-4">
        {lines.map((line, i) => (
          <p key={i} className="text-center text-gray-200 text-sm leading-relaxed">
            {line}
          </p>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════ */
/*                        KaraokeQuestion                            */
/* ═══════════════════════════════════════════════════════════════════ */

const KaraokeQuestion = ({
  round,
  onAnswerSubmit,
  hasAnswered,
  selectedAnswer,
  showResults,
  roundResults,
}: Props) => {
  // Audio plays during the round (like Classique), not only on results
  const audio = useAudioPlayer(round, showResults);

  const syncedLines: SyncedLine[] = round.extra_data?.synced_lyrics ?? [];
  const plainLines: string[] = round.extra_data?.plain_lyrics_lines ?? [];
  const hasSynced = syncedLines.length > 0;

  const activeIndex = useLyricSync(syncedLines, round, showResults);

  return (
    <div className="bg-white rounded-lg shadow-xl p-8">
      {/* Header */}
      <div className="mb-6 text-center">
        <div className="text-4xl mb-2">🎤</div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          {round.question_text || 'Écoutez le karaoké et devinez le titre !'}
        </h2>
        {!showResults && (
          <p className="text-gray-500 text-sm">
            Les paroles défilent en rythme — devinez le titre !
          </p>
        )}
      </div>

      {/* Audio player */}
      <div className="mb-6">
        <AudioPlayerUI
          {...audio}
          label={hasSynced ? '🎤 Karaoké en cours…' : '🎵 Écoutez attentivement…'}
        />
      </div>

      {/* Lyrics display */}
      {!showResults && hasSynced && (
        <LyricsScroller lines={syncedLines} activeIndex={activeIndex} />
      )}
      {!showResults && !hasSynced && plainLines.length > 0 && (
        <PlainLyricsDisplay lines={plainLines} />
      )}

      {/* Track reveal on results */}
      {showResults && <TrackReveal round={round} />}

      {/* MCQ options */}
      <OptionsGrid
        options={round.options}
        hasAnswered={hasAnswered}
        showResults={showResults}
        selectedAnswer={selectedAnswer}
        roundResults={roundResults}
        onOptionClick={onAnswerSubmit}
      />

      <ResultFooter
        showResults={showResults}
        roundResults={roundResults}
        selectedAnswer={selectedAnswer}
        hasAnswered={hasAnswered}
      />
    </div>
  );
};

export default KaraokeQuestion;
