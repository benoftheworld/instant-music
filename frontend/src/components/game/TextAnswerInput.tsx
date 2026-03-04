import { useState, useRef } from 'react';
import { formatAnswer } from '@/utils/formatAnswer';

interface TextAnswerInputProps {
  onSubmit: (answer: string) => void;
  hasAnswered: boolean;
  selectedAnswer: string | null;
  showResults: boolean;
  roundResults: { correct_answer: string; points_earned?: number } | null;
  placeholder?: string;
  label?: string;
  /** When true, hints the user to provide artist and title (in any order). */
  dualInput?: boolean;
}

/**
 * TextAnswerInput – Free-text input for text answer mode.
 * Used instead of MCQ options when game.answer_mode === 'text'.
 *
 * In dualInput mode the user types freely in a single field. They can provide
 * artist and/or title separated by a dash, slash, or pipe — in any order.
 * Knowing only one of the two still earns points.
 * The backend handles order-agnostic fuzzy matching.
 */
export default function TextAnswerInput({
  onSubmit,
  hasAnswered,
  selectedAnswer,
  showResults,
  roundResults,
  placeholder = 'Tapez votre réponse...',
  label = 'Votre réponse',
  dualInput = false,
}: TextAnswerInputProps) {
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = () => {
    if (hasAnswered) return;
    const trimmed = inputValue.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
  };

  const getResultStyle = () => {
    if (!showResults || !roundResults) return '';
    if (selectedAnswer && roundResults.points_earned && roundResults.points_earned > 0) {
      return 'border-green-500 bg-green-50';
    }
    return 'border-red-500 bg-red-50';
  };

  /** Format the displayed answer — handles legacy JSON & plain text. */
  const getDisplayAnswer = () => {
    if (!selectedAnswer) return null;
    return formatAnswer(selectedAnswer);
  };

  const dualPlaceholder = 'Artiste - Titre (dans n\'importe quel ordre)';

  return (
    <div className="mb-6">
      {!hasAnswered && !showResults ? (
        <div className="space-y-3">
          <label className="block text-sm font-medium text-gray-700">
            {dualInput ? '🎤 Artiste et/ou 🎵 Titre' : label}
          </label>
          <div className="flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
              placeholder={dualInput ? dualPlaceholder : placeholder}
              className="flex-1 px-4 py-3 text-lg border-2 border-gray-300 rounded-xl
                         focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200
                         transition-all"
              autoFocus
              maxLength={200}
            />
            <button
              onClick={handleSubmit}
              disabled={!inputValue.trim()}
              className="px-6 py-3 bg-primary-600 text-white rounded-xl font-bold text-lg
                         hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed
                         shadow-lg hover:shadow-xl"
            >
              Valider
            </button>
          </div>
          <p className="text-xs text-gray-400">
            {dualInput
              ? 'Séparez artiste et titre par un tiret, slash ou pipe • L\'ordre n\'importe pas • Un seul suffit pour marquer des points'
              : 'Appuyez sur Entrée pour valider • Les accents et articles sont tolérés'}
          </p>
        </div>
      ) : hasAnswered && !showResults ? (
        <div className="text-center py-4">
          <div className="inline-block bg-blue-100 text-blue-800 px-6 py-3 rounded-xl text-lg font-semibold mb-2">
            « {getDisplayAnswer()} »
          </div>
          <div className="text-gray-500 animate-pulse mt-2">
            En attente des autres joueurs...
          </div>
        </div>
      ) : null}

      {/* Show results */}
      {showResults && roundResults && (
        <div className={`p-4 rounded-xl border-2 transition-all ${getResultStyle()}`}>
          {selectedAnswer && (
            <p className="text-lg mb-2">
              Votre réponse : <span className="font-bold">« {getDisplayAnswer()} »</span>
            </p>
          )}
          <p className="text-lg font-bold">
            Bonne réponse : <span className="text-green-700">« {roundResults.correct_answer} »</span>
          </p>
          {roundResults.points_earned !== undefined && roundResults.points_earned > 0 ? (
            <p className="text-green-600 font-bold mt-2">
              ✓ Bravo ! +{roundResults.points_earned} points
            </p>
          ) : selectedAnswer ? (
            <p className="text-red-600 font-bold mt-2">
              ✗ Dommage !
            </p>
          ) : (
            <p className="text-gray-500 font-bold mt-2">
              ⏱ Temps écoulé !
            </p>
          )}
        </div>
      )}
    </div>
  );
}
