import React from 'react';
import {
  useAudioPlayer, AudioPlayerUI, QuestionHeader, OptionsGrid, ResultFooter, TrackReveal,
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
      <QuestionHeader
        icon={showResults ? '🎶' : icon}
        title={round.question_text || defaultTitle}
        subtitle={subtitle}
        audioStatus={!showResults ? <AudioPlayerUI compact {...audio} label={audioLabel} /> : undefined}
      />

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
