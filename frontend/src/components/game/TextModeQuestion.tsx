import {
  useAudioPlayer,
  useAudioPlayerOnResults,
  AudioPlayerUI,
  type Props,
} from './shared';
import TextAnswerInput from './TextAnswerInput';

interface TextModeQuestionProps extends Props {
  /** Placeholder text for the input field */
  placeholder?: string;
}

/**
 * TextModeQuestion – Renders the question header, audio player, and a free-text
 * input instead of the MCQ options grid.
 *
 * For lyrics mode the audio only plays after results are revealed (same
 * behaviour as LyricsQuestion).  For every other mode the audio plays during
 * the round.
 */
export default function TextModeQuestion({
  round,
  onAnswerSubmit,
  hasAnswered,
  selectedAnswer,
  showResults,
  roundResults,
  seekOffsetMs = 0,
  placeholder,
}: TextModeQuestionProps) {
  const isLyrics = round.question_type === 'lyrics';
  const isIntro = round.question_type === 'intro';
  const audioDuration = isIntro ? (round.extra_data?.audio_duration || 5) : undefined;

  // For lyrics: audio only on results.  For everything else: audio during the round.
  const duringRoundAudio = useAudioPlayer(round, showResults, audioDuration, seekOffsetMs);
  const resultsOnlyAudio = useAudioPlayerOnResults(round, showResults);
  const audio = isLyrics ? resultsOnlyAudio : duringRoundAudio;

  const getModeIcon = () => {
    switch (round.question_type) {
      case 'blind_inverse': return '🎯';
      case 'guess_year': return '📅';
      case 'guess_artist': return '🎤';
      case 'intro': return '⚡';
      case 'lyrics': return '📝';
      default: return '🎵';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-xl p-8">
      {/* Question header */}
      <div className="mb-6 text-center">
        <div className="text-4xl mb-3">{getModeIcon()}</div>
        <h2 className="text-2xl font-bold text-gray-800">
          {round.question_text}
        </h2>
        {round.question_type === 'blind_inverse' && (
          <div className="inline-block bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-6 py-3 rounded-full text-lg font-bold mt-3 shadow-lg">
            🎤 {round.artist_name}
          </div>
        )}
        {round.question_type === 'guess_artist' && (
          <p className="text-gray-600 mt-2">
            Titre : <span className="font-semibold">{round.track_name}</span>
          </p>
        )}
        {round.question_type === 'lyrics' && (
          <p className="text-gray-600 mt-1">
            <span className="font-semibold">{round.track_name}</span> — {round.artist_name}
          </p>
        )}
        {isIntro && (
          <div className="inline-block bg-gradient-to-r from-yellow-400 to-red-500 text-white px-4 py-1 rounded-full text-sm font-bold mt-3 shadow">
            ⚡ {audioDuration} secondes d&apos;écoute
          </div>
        )}
      </div>

      {/* Audio player (during round for non-lyrics, after results for lyrics) */}
      {!isLyrics && !showResults && (
        <div className="mb-6">
          <AudioPlayerUI {...audio} />
        </div>
      )}

      {/* Lyrics: show audio on results */}
      {isLyrics && showResults && (
        <div className="mb-6">
          <AudioPlayerUI {...audio} label="Écoutez la chanson..." />
        </div>
      )}

      {/* Lyrics snippet for lyrics mode */}
      {round.question_type === 'lyrics' && round.extra_data?.lyrics_snippet && (
        <div className="mb-6 p-6 bg-gray-50 rounded-xl border-2 border-gray-200 text-center">
          <p className="text-xl leading-relaxed font-medium text-gray-800 italic">
            &quot;{round.extra_data.lyrics_snippet.split('_____').map((part: string, i: number, arr: string[]) => (
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

      {/* Text answer input */}
      <TextAnswerInput
        onSubmit={onAnswerSubmit}
        hasAnswered={hasAnswered}
        selectedAnswer={selectedAnswer}
        showResults={showResults}
        roundResults={roundResults}
        placeholder={placeholder}
      />
    </div>
  );
}
