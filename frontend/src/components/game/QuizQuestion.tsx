import {
  useAudioPlayer, AudioPlayerUI, OptionsGrid, ResultFooter, TrackReveal,
  type Props,
} from './shared';

/**
 * QuizQuestion – Default classique mode (and fallback for unknown modes).
 * Plays audio, shows 4 options, player picks the correct title.
 */
const QuizQuestion = ({
  round,
  onAnswerSubmit,
  hasAnswered,
  selectedAnswer,
  showResults,
  roundResults,
  seekOffsetMs = 0,
  excludedOptions = [],
  fogBlur = false,
}: Props) => {
  const audio = useAudioPlayer(round, showResults, undefined, seekOffsetMs);

  return (
    <div className="bg-white rounded-lg shadow-xl p-4 md:p-8">
      <div className="mb-3 md:mb-6 text-center">
        <div className="text-2xl md:text-4xl mb-1 md:mb-3">🎵</div>
        <h2 className="text-lg md:text-2xl font-bold text-gray-800">
          {round.question_text || 'Quel est le titre de ce morceau ?'}
        </h2>
        <p className="text-gray-500 text-xs md:text-sm mt-1 md:mt-2">
          L'artiste sera révélé à la fin du round
        </p>
      </div>

      {!showResults && (
        <div className="mb-3 md:mb-6">
          <AudioPlayerUI {...audio} />
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
        excludedOptions={excludedOptions}
        fogBlur={fogBlur}
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

export default QuizQuestion;
