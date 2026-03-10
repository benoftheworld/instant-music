import React from 'react';
import {
  useAudioPlayer, AudioPlayerUI, OptionsGrid, ResultFooter,
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
      <div className="mb-6 rounded-lg overflow-hidden shadow-lg bg-primary-600 p-6">
        <div className="text-white text-center">
          {!showResults && (
            <AudioPlayerUI compact {...audio} label={audioLabel} />
          )}
          <p className="text-lg font-bold">{round.question_text || defaultTitle}</p>
          <p className="text-sm opacity-80">{subtitle}</p>
        </div>
      </div>

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
