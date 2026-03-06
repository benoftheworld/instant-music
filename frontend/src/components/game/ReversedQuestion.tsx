import {
  useReverseAudioPlayer, AudioPlayerUI, OptionsGrid, ResultFooter, TrackReveal,
  type Props,
} from './shared';

/**
 * ReversedQuestion – Mode "À l'envers" : la musique joue en sens inverse.
 * Utilise le Web Audio API pour inverser les échantillons PCM avant lecture.
 * Le joueur doit reconnaître le morceau joué à l'envers.
 */
const ReversedQuestion = ({
  round,
  onAnswerSubmit,
  hasAnswered,
  selectedAnswer,
  showResults,
  roundResults,
  excludedOptions = [],
  fogBlur = false,
}: Props) => {
  const audio = useReverseAudioPlayer(round, showResults);

  return (
    <div className="bg-white rounded-lg shadow-xl p-4 md:p-8">
      <div className="mb-3 md:mb-6 text-center">
        <div className="text-2xl md:text-4xl mb-1 md:mb-3">🔄</div>
        <h2 className="text-lg md:text-2xl font-bold text-gray-800">
          {round.question_text || 'Quel est le titre de ce morceau ?'}
        </h2>
        <p className="text-gray-500 text-xs md:text-sm mt-1 md:mt-2">
          La musique joue à l'envers — saurez-vous la reconnaître ?
        </p>
      </div>

      {!showResults && (
        <div className="mb-3 md:mb-6">
          <AudioPlayerUI {...audio} label="Écoutez attentivement... (à l'envers)" />
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

export default ReversedQuestion;
