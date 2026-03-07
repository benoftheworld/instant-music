import { useState } from 'react';
import {
  useAudioPlayer, AudioPlayerUI, TrackReveal, OptionsGrid, ResultFooter,
  type Props,
} from './shared';

/**
 * YearQuestion – Player guesses the release year of a track.
 * In MCQ mode (options provided): shows 4 year choices.
 * In text mode (no options): free numeric input with ±2 tolerance.
 */
const YearQuestion = ({
  round,
  onAnswerSubmit,
  hasAnswered,
  selectedAnswer,
  showResults,
  roundResults,
  seekOffsetMs = 0,
  excludedOptions = [],
  fogBlur = false,
}: Props) => {
  const audio = useAudioPlayer(round, showResults, undefined, seekOffsetMs);
  const [yearInput, setYearInput] = useState('');

  const isMcqMode = round.options && round.options.length > 0;

  const correctYear = parseInt(roundResults?.correct_answer || round.extra_data?.year || '0');
  const givenYear = parseInt(selectedAnswer || '0');
  const diff = Math.abs(givenYear - correctYear);

  const handleSubmit = () => {
    if (!yearInput || hasAnswered) return;
    onAnswerSubmit(yearInput);
  };

  const getResultColor = () => {
    if (!showResults) return '';
    if (diff === 0) return 'text-green-600';
    if (diff <= 2) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getResultMessage = () => {
    if (diff === 0) return `✓ Exact ! C'est bien ${correctYear}`;
    if (diff === 1) return `≈ Presque ! C'était ${correctYear} (±1 an)`;
    if (diff === 2) return `≈ Pas mal ! C'était ${correctYear} (±2 ans)`;
    return `✗ Raté ! C'était ${correctYear}`;
  };

  return (
    <div className="bg-white rounded-lg shadow-xl p-8">
      {/* Question header */}
      <div className="mb-6 text-center">
        <div className="text-4xl mb-3">📅</div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          {round.question_text || 'En quelle année est sorti ce morceau ?'}
        </h2>
      </div>

      {/* Audio player */}
      {!showResults && (
        <div className="mb-6">
          <AudioPlayerUI {...audio} />
        </div>
      )}

      {showResults && <TrackReveal round={round} />}

      {/* MCQ mode: show year options as buttons */}
      {isMcqMode ? (
        <>
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
        </>
      ) : (
        <>
          {/* Text mode: free numeric input */}
          <div className="mb-6">
            {!hasAnswered && !showResults ? (
              <div className="flex flex-col items-center gap-4">
                <input
                  type="number"
                  min="1950"
                  max="2030"
                  placeholder="Ex: 2015"
                  value={yearInput}
                  onChange={(e) => setYearInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
                  className="w-48 text-center text-4xl font-bold p-4 border-4 border-blue-300 rounded-xl
                             focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  autoFocus
                />
                <button
                  onClick={handleSubmit}
                  disabled={!yearInput}
                  className="px-8 py-3 bg-blue-600 text-white rounded-lg font-bold text-lg
                             hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Valider
                </button>
                <p className="text-sm text-gray-500">
                  Tolérance : ±2 ans
                </p>
              </div>
            ) : hasAnswered && !showResults ? (
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-600 mb-2">{selectedAnswer}</div>
                <div className="text-lg text-gray-600 animate-pulse">
                  En attente des autres joueurs...
                </div>
              </div>
            ) : null}
          </div>

          {/* Results for text mode */}
          {showResults && roundResults && (
            <div className="mt-6 p-4 rounded-lg bg-blue-50 border-2 border-blue-200 text-center">
              <p className="text-lg mb-1">
                Votre réponse : <span className="font-bold">{selectedAnswer || '—'}</span>
              </p>
              <p className={`text-xl font-bold mt-2 ${getResultColor()}`}>
                {getResultMessage()}
              </p>
              {roundResults.points_earned !== undefined && roundResults.points_earned > 0 && (
                <p className="text-green-600 font-bold mt-2">
                  +{roundResults.points_earned} points
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default YearQuestion;
