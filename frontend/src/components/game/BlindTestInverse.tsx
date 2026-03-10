import {
  useAudioPlayer, AudioPlayerUI, OptionsGrid, ResultFooter, TrackReveal,
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
      <div className="flex items-center gap-3 mb-3 md:mb-4 shrink-0">
        <div className="w-12 h-12 shrink-0 rounded-lg bg-gradient-to-r from-yellow-400 to-orange-500 flex items-center justify-center shadow">
          <span className="text-2xl">🎤</span>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-bold text-orange-500 truncate">{round.artist_name}</p>
          <h2 className="text-sm md:text-base font-bold text-gray-800 leading-tight">
            {round.question_text || 'Quel est le titre de ce morceau ?'}
          </h2>
        </div>
        {!showResults && <AudioPlayerUI compact {...audio} />}
      </div>

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
