import { useEffect } from 'react';
import {
  useAudioPlayer, OptionsGrid, ResultFooter, TrackReveal,
  type Props,
} from './shared';

/**
 * IntroQuestion – Same as classic quiz but audio stops after 5 seconds.
 * Player must recognize the track from just the intro.
 * No "Lancer la musique" button to prevent cheating.
 */
const IntroQuestion = ({
  round,
  onAnswerSubmit,
  hasAnswered,
  selectedAnswer,
  showResults,
  roundResults,
  seekOffsetMs = 0,
}: Props) => {
  const audioDuration = round.extra_data?.audio_duration || 5;
  const audio = useAudioPlayer(round, showResults, audioDuration, seekOffsetMs);
  const { needsPlay, isPlaying, handlePlay, playerError } = audio;

  // Auto-trigger play when browser blocks autoplay (no manual button in Rapide)
  useEffect(() => {
    if (needsPlay && !isPlaying) {
      handlePlay();
    }
  }, [needsPlay, isPlaying, handlePlay]);

  // Also trigger play on any click within the component
  const handleCardClick = () => {
    if (needsPlay && !isPlaying) {
      handlePlay();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-xl p-4 md:p-8" onClick={handleCardClick}>
      {/* Header with lightning bolt */}
      <div className="mb-3 md:mb-6 text-center">
        <div className="inline-block bg-gradient-to-r from-yellow-400 to-red-500 text-white px-4 py-1 rounded-full text-sm font-bold mb-2 md:mb-3 shadow">
          ⚡ {audioDuration} secondes d&apos;écoute
        </div>
        <h2 className="text-lg md:text-2xl font-bold text-gray-800 mb-1 md:mb-2">
          {round.question_text || 'Reconnaissez ce morceau !'}
        </h2>
      </div>

      {!showResults && (
        <div className="mb-3 md:mb-6">
          <div className="flex flex-col items-center justify-center p-3 md:p-6 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg min-h-[80px] md:min-h-[120px]">
            {playerError ? (
              <div className="text-white text-center">
                <div className="text-4xl mb-2">⚠️</div>
                <p className="text-sm mb-1">{playerError}</p>
              </div>
            ) : isPlaying ? (
              <div className="text-white text-center">
                <div className="text-4xl mb-2 animate-pulse">🎵</div>
                <p className="text-sm">Intro — {audioDuration}s seulement !</p>
              </div>
            ) : (
              <div className="text-white text-center">
                <div className="text-4xl mb-2">⏳</div>
                <p className="text-sm">
                  {needsPlay ? 'Cliquez n\u2019importe où pour lancer l\u2019intro...' : 'Chargement de l\u2019intro...'}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {showResults && <TrackReveal round={round} />}

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

export default IntroQuestion;
