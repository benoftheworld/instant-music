import {
  useAudioPlayerOnResults, AudioPlayerUI, OptionsGrid, ResultFooter, TrackReveal,
  type Props,
} from './shared';

/**
 * LyricsQuestion – A line of lyrics with a word blanked out.
 * Player picks the correct word from 4 options.
 * Audio only plays AFTER showing results.
 */
const LyricsQuestion = ({
  round,
  onAnswerSubmit,
  hasAnswered,
  selectedAnswer,
  showResults,
  roundResults,
  excludedOptions = [],
  fogBlur = false,
}: Props) => {
  // For Lyrics mode: only play audio when showing results
  const audio = useAudioPlayerOnResults(round, showResults);
  const snippet: string = round.extra_data?.lyrics_snippet || '';

  // If no lyrics fallback to standard quiz display
  const isLyricsMode = !!snippet;

  return (
    <div className="bg-white rounded-lg shadow-xl p-3 md:p-6 flex flex-col flex-1 min-h-0">
      {/* Header */}
      <div className="mb-2 md:mb-4 text-center shrink-0">
        <div className="text-xl md:text-3xl mb-1">📝</div>
        <h2 className="text-base md:text-xl font-bold text-gray-800">
          {round.question_text || 'Complétez les paroles'}
        </h2>
        <p className="text-gray-600 text-xs md:text-sm">
          <span className="font-semibold">{round.track_name}</span> — {round.artist_name}
        </p>
      </div>

      {/* Show track reveal AND audio player when results are shown */}
      {showResults && (
        <>
          <TrackReveal round={round} />
          <div className="mb-3 md:mb-6">
            <AudioPlayerUI {...audio} label="Écoutez la chanson..." />
          </div>
        </>
      )}

      {/* Lyrics snippet with blank */}
      {isLyricsMode && (
        <div className="mb-2 md:mb-4 p-2 md:p-4 bg-gray-50 rounded-xl border-2 border-gray-200 text-center shrink-0">
          <p className="text-sm md:text-lg leading-relaxed font-medium text-gray-800 italic">
            &quot;{snippet.split('_____').map((part, i, arr) => (
              <span key={i}>
                {part}
                {i < arr.length - 1 && (
                  <span className="inline-block mx-1 px-3 py-1 bg-yellow-200 rounded font-bold text-yellow-800 not-italic">
                    {showResults && roundResults ? roundResults.correct_answer : '???'}
                  </span>
                )}
              </span>
            ))}&quot;
          </p>
        </div>
      )}

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

export default LyricsQuestion;
