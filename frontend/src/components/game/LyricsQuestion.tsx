import {
  useAudioPlayerOnResults, AudioPlayerUI, QuestionHeader, OptionsGrid, ResultFooter,
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
      <QuestionHeader
        icon="📝"
        title={round.question_text || 'Complétez les paroles'}
        subtitle={`${round.track_name} — ${round.artist_name}`}
        audioStatus={showResults ? <AudioPlayerUI compact {...audio} /> : undefined}
      />

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
