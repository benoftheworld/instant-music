import { soundEffects } from '../../services/soundEffects';
import type { RoundResults } from './types';

export function OptionsGrid({
  options,
  hasAnswered,
  showResults,
  selectedAnswer,
  roundResults,
  onOptionClick,
  excludedOptions = [],
  fogBlur = false,
}: {
  options: string[];
  hasAnswered: boolean;
  showResults: boolean;
  selectedAnswer: string | null;
  roundResults: RoundResults | null;
  onOptionClick: (option: string) => void;
  excludedOptions?: string[];
  fogBlur?: boolean;
}) {
  const visibleOptions = showResults
    ? options
    : options.filter((o) => !excludedOptions.includes(o));

  const getStyle = (option: string) => {
    if (!hasAnswered && !showResults)
      return 'bg-white hover:bg-primary-100 border-2 border-cream-300 hover:border-primary-500 cursor-pointer';
    if (hasAnswered && !showResults) {
      if (option === selectedAnswer) return 'bg-primary-500 text-white border-2 border-primary-700';
      return 'bg-gray-200 border-2 border-gray-300 cursor-not-allowed';
    }
    if (showResults && roundResults) {
      if (option === roundResults.correct_answer)
        return 'bg-green-500 text-white border-2 border-green-700 ring-4 ring-green-300 scale-[1.02]';
      if (option === selectedAnswer) return 'bg-red-500 text-white border-2 border-red-700';
      return 'bg-gray-200 border-2 border-gray-300';
    }
    return 'bg-white border-2 border-gray-300';
  };

  const isBlurred = fogBlur && !hasAnswered && !showResults;

  return (
    <div
      className={`grid grid-cols-1 sm:grid-cols-2 gap-2 md:gap-3 mb-4 md:mb-6 transition-[filter] duration-1000${
        isBlurred ? ' blur-sm select-none' : ''
      }`}
    >
      {visibleOptions.map((option, index) => (
        <button
          key={index}
          onClick={() => {
            if (!hasAnswered && !showResults) {
              soundEffects.click();
              onOptionClick(option);
            }
          }}
          className={`p-3 md:p-5 rounded-xl text-left transition-all duration-300 ${getStyle(option)}`}
          disabled={hasAnswered || showResults}
        >
          <div className="flex items-center gap-2 md:gap-3">
            <div className="w-7 h-7 md:w-8 md:h-8 shrink-0 rounded-full bg-primary-500 text-white flex items-center justify-center font-bold text-xs md:text-sm">
              {String.fromCharCode(65 + index)}
            </div>
            <span className="text-sm md:text-lg font-medium leading-tight break-words">{option}</span>
          </div>
        </button>
      ))}
    </div>
  );
}
