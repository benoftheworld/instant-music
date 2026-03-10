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
    <div className="bg-white rounded-xl shadow-xl p-4 md:p-6 flex flex-col flex-1 min-h-0">
      {/* Compact header row */}
      <div className="flex items-center gap-3 mb-3 md:mb-4 shrink-0">
        <div className="w-12 h-12 shrink-0 rounded-lg bg-gradient-to-br from-primary-600 to-primary-400 flex items-center justify-center shadow">
          <span className="text-2xl">📝</span>
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-sm md:text-base font-bold text-gray-800 leading-tight">
            {round.question_text || 'Complétez les paroles'}
          </h2>
          <p className="text-gray-400 text-xs truncate">
            <span className="font-semibold">{round.track_name}</span> — {round.artist_name}
          </p>
        </div>
        {showResults && <AudioPlayerUI compact {...audio} />}
      </div>

      {/* Show track reveal when results are shown */}
      {showResults && <TrackReveal round={round} />}

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
