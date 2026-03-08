import {
  useAudioPlayer, AudioPlayerUI, OptionsGrid, ResultFooter, TrackReveal,
  type Props,
} from './shared';

/**
 * SlowQuestion – Mode "Mollo" : la musique joue à 0.3× de sa vitesse normale.
 * Le joueur doit reconnaître le morceau malgré le tempo ralenti.
 */
const SlowQuestion = ({
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
  const audio = useAudioPlayer(round, showResults, undefined, seekOffsetMs, 0.3);

  return (
    <div className="bg-white rounded-lg shadow-xl p-3 md:p-6 flex flex-col flex-1 min-h-0">
      <div className="mb-2 md:mb-4 text-center shrink-0">
        <div className="text-xl md:text-3xl mb-1 md:mb-2">🦥</div>
        <h2 className="text-base md:text-xl font-bold text-gray-800">
          {round.question_text || 'Quel est le titre de ce morceau ?'}
        </h2>
        <p className="text-gray-500 text-xs mt-0.5 md:mt-1">
          La musique joue au ralenti — saurez-vous la reconnaître ?
        </p>
      </div>

      {!showResults && (
        <div className="mb-2 md:mb-4 shrink-0">
          <AudioPlayerUI {...audio} label="Écoutez attentivement... (ralenti)" />
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

export default SlowQuestion;
