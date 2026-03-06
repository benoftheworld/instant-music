import {
  useAudioPlayer, AudioPlayerUI, OptionsGrid, ResultFooter, TrackReveal,
  type Props,
} from './shared';

/**
 * GuessArtistQuestion – Player hears audio and must identify the artist.
 */
const GuessArtistQuestion = ({
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
      {/* Header */}
      <div className="mb-3 md:mb-6 text-center">
        <div className="text-2xl md:text-4xl mb-1 md:mb-2">🎤</div>
        <h2 className="text-lg md:text-2xl font-bold text-gray-800 mb-1 md:mb-2">
          {round.question_text || 'Qui interprète ce morceau ?'}
        </h2>
      </div>

      {/* Audio player */}
      {!showResults && (
        <div className="mb-3 md:mb-6">
          <AudioPlayerUI {...audio} label="Écoutez et trouvez l'artiste..." />
        </div>
      )}

      {showResults && <TrackReveal round={round} />}

      {/* Options */}
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

export default GuessArtistQuestion;
