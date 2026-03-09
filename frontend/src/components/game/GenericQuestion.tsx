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
    <div className="bg-white rounded-xl shadow-xl p-4 md:p-8 flex flex-col flex-1 min-h-0">
      <div className="mb-2 md:mb-4 text-center shrink-0">
        <div className="text-xl md:text-3xl mb-1 md:mb-2">{icon}</div>
        <h2 className="text-lg md:text-2xl font-bold text-gray-800">
          {round.question_text || defaultTitle}
        </h2>
        {subtitle && (
          <p className="text-gray-500 text-xs mt-0.5 md:mt-1">{subtitle}</p>
        )}
      </div>

      {!showResults && (
        <div className="mb-2 md:mb-4 shrink-0">
          <AudioPlayerUI {...audio} label={audioLabel} />
        </div>
      )}

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
