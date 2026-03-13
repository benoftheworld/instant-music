import { useEffect } from 'react';
import {
  useAudioPlayer,
  useAudioPlayerOnResults,
  AudioPlayerUI,
  QuestionHeader,
  type Props,
} from './shared';
import TextAnswerInput from './TextAnswerInput';
import LyricsSnippet from './LyricsSnippet';

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
  const isIntro = round.extra_data?.audio_duration != null && round.extra_data?.audio_duration <= 5;
  const audioDuration = isIntro ? (round.extra_data?.audio_duration || 3) : undefined;

  // For lyrics: audio only on results.  For everything else: audio during the round.
  const duringRoundAudio = useAudioPlayer(round, showResults, audioDuration, seekOffsetMs);
  const resultsOnlyAudio = useAudioPlayerOnResults(round, showResults);
  const audio = isLyrics ? resultsOnlyAudio : duringRoundAudio;
  const { needsPlay, isPlaying, handlePlay } = audio;

  // Auto-trigger play for Rapide/Intro mode to prevent cheating
  useEffect(() => {
    if (isIntro && needsPlay && !isPlaying) {
      handlePlay();
    }
  }, [isIntro, needsPlay, isPlaying, handlePlay]);

  // Click handler to trigger play for Rapide mode (fallback if auto-trigger fails)
  const handleCardClick = () => {
    if (isIntro && needsPlay && !isPlaying) {
      handlePlay();
    }
  };

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
    <div className="bg-white rounded-xl shadow-xl p-4 md:p-6" onClick={handleCardClick}>
      <QuestionHeader
        icon={getModeIcon()}
        title={round.question_text}
        subtitle={
          round.question_type === 'blind_inverse' ? round.artist_name
          : round.question_type === 'guess_artist' ? `Titre : ${round.track_name}`
          : round.question_type === 'lyrics' ? `${round.track_name} — ${round.artist_name}`
          : undefined
        }
        gradientFrom={round.question_type === 'blind_inverse' ? 'from-yellow-400' : undefined}
        gradientTo={round.question_type === 'blind_inverse' ? 'to-orange-500' : undefined}
        badge={isIntro ? (
          <span className="inline-block bg-gradient-to-r from-yellow-400 to-red-500 text-white px-2 py-0.5 rounded-full text-xs font-bold">
            ⚡ {audioDuration}s
          </span>
        ) : undefined}
        audioStatus={(
          ((!isLyrics && !showResults) || (isLyrics && showResults))
            ? <AudioPlayerUI compact {...audio} hideManualPlay={isIntro} />
            : undefined
        )}
      />

      {/* Lyrics snippet for lyrics mode */}
      {round.question_type === 'lyrics' && round.extra_data?.lyrics_snippet && (
        <LyricsSnippet
          snippet={round.extra_data.lyrics_snippet}
          correctAnswer={roundResults?.correct_answer}
          showAnswer={showResults && !!roundResults}
          className="mb-6"
        />
      )}

      {/* Text answer input */}
      {/* For classique/rapide modes (guess_title, guess_artist), enable dual input (title + artist) */}
      <TextAnswerInput
        onSubmit={onAnswerSubmit}
        hasAnswered={hasAnswered}
        selectedAnswer={selectedAnswer}
        showResults={showResults}
        roundResults={roundResults}
        placeholder={placeholder}
        dualInput={round.question_type === 'guess_title' || round.question_type === 'guess_artist'}
      />
    </div>
  );
}
