import React from 'react';
import {
  useAudioPlayer, AudioPlayerUI, OptionsGrid, ResultFooter, TrackReveal,
  type Props,
} from './shared';

interface GenericQuestionProps extends Props {
  icon: string;
  defaultTitle: string;
  subtitle?: string;
  audioLabel?: string;
  playbackRate?: number;
}

const GenericQuestion = ({
  icon,
  defaultTitle,
  subtitle,
  audioLabel,
  playbackRate,
  round,
  onAnswerSubmit,
  hasAnswered,
  selectedAnswer,
  showResults,
  roundResults,
  seekOffsetMs = 0,
  excludedOptions = [],
  fogBlur = false,
}: GenericQuestionProps) => {
  const audio = useAudioPlayer(round, showResults, undefined, seekOffsetMs, playbackRate);

  return (
    <div className="bg-white rounded-xl shadow-xl p-4 md:p-6 flex flex-col flex-1 min-h-0">
      {/* Compact header row */}
      <div className="flex items-center gap-3 mb-3 md:mb-4 shrink-0">
        <div className="w-12 h-12 shrink-0 rounded-lg bg-gradient-to-br from-primary-600 to-primary-400 flex items-center justify-center shadow">
          <span className={`text-2xl${!showResults && audio.isPlaying ? ' animate-pulse' : ''}`}>
            {showResults ? '🎶' : icon}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-sm md:text-base font-bold text-gray-800 leading-tight">
            {round.question_text || defaultTitle}
          </h2>
          {subtitle && (
            <p className="text-gray-400 text-xs mt-0.5 truncate">{subtitle}</p>
          )}
        </div>
        {!showResults && (
          <AudioPlayerUI compact {...audio} label={audioLabel} />
        )}
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

export default React.memo(GenericQuestion);
