import {
  useAudioPlayer, AudioPlayerUI, QuestionHeader, OptionsGrid, ResultFooter, TrackReveal,
  type Props,
} from './shared';

/**
 * BlindTestInverse – The artist is given prominently.
 * Player must guess the correct song title from 4 options.
 */
const BlindTestInverse = ({
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
    <div className="bg-white rounded-xl shadow-xl p-4 md:p-6 flex flex-col flex-1 min-h-0">
      <QuestionHeader
        icon="🎤"
        title={round.question_text || 'Quel est le titre de ce morceau ?'}
        subtitle={round.artist_name}
        gradientFrom="from-yellow-400"
        gradientTo="to-orange-500"
        audioStatus={!showResults ? <AudioPlayerUI compact {...audio} /> : undefined}
      />

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

export default BlindTestInverse;
