import {
  useAudioPlayerOnResults, AudioPlayerUI, OptionsGrid, ResultFooter, TrackReveal,
  type Props,
} from './shared';
import LyricsSnippet from './LyricsSnippet';

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
    <div className="bg-white rounded-xl shadow-xl p-4 md:p-8 flex flex-col flex-1 min-h-0">
      {/* Header */}
      <div className="mb-2 md:mb-4 text-center shrink-0">
        <div className="text-xl md:text-3xl mb-1">📝</div>
        <h2 className="text-lg md:text-2xl font-bold text-gray-800">
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
        <LyricsSnippet
          snippet={snippet}
          correctAnswer={roundResults?.correct_answer}
          showAnswer={showResults && !!roundResults}
          className="mb-2 md:mb-4"
        />
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
