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
}: Props) => {
  const audio = useAudioPlayer(round, showResults, undefined, seekOffsetMs);

  return (
    <div className="bg-white rounded-lg shadow-xl p-8">
      <div className="mb-6 text-center">
        <div className="text-4xl mb-3">🎵</div>
        <h2 className="text-2xl font-bold text-gray-800">
          {round.question_text || 'Quel est le titre de ce morceau ?'}
        </h2>
        <p className="text-gray-500 text-sm mt-2">
          L'artiste sera révélé à la fin du round
        </p>
      </div>

      {!showResults && (
        <div className="mb-6">
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
