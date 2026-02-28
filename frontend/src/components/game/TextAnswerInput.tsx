import { useState, useRef, useEffect } from 'react';

interface TextAnswerInputProps {
  onSubmit: (answer: string) => void;
  hasAnswered: boolean;
  selectedAnswer: string | null;
  showResults: boolean;
  roundResults: { correct_answer: string; points_earned?: number } | null;
  placeholder?: string;
  label?: string;
  /** When true, shows sequential single input for artist then title */
  dualInput?: boolean;
}

/**
 * TextAnswerInput – Free-text input for text answer mode.
 * Used instead of MCQ options when game.answer_mode === 'text'.
 * In dualInput mode, shows a single input sequentially: artist first, then title.
 * The backend is called only once (after both are entered) to respect unique_together.
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

  // Dual-input sequential state
  // dualStep 0 = entering artist, dualStep 1 = entering title
  const [dualStep, setDualStep] = useState<0 | 1>(0);
  const [submittedArtist, setSubmittedArtist] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus input when advancing to step 1
  useEffect(() => {
    if (dualInput && dualStep === 1) {
      inputRef.current?.focus();
    }
  }, [dualInput, dualStep]);

  // Edge case: round ends (showResults=true) while user is at step 1 (artist entered but no title yet).
  // Submit the partial answer so the backend receives at least the artist.
  useEffect(() => {
    if (dualInput && showResults && dualStep === 1 && !hasAnswered) {
      const artist = submittedArtist ?? '';
      if (artist) {
        onSubmit(JSON.stringify({ artist, title: '' }));
      }
    }
    // We intentionally only react to showResults flipping to true
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showResults]);

  const handleSubmit = () => {
    if (hasAnswered) return;

    if (dualInput) {
      if (dualStep === 0) {
        // Store artist (may be empty if user doesn't know), advance to title step
        setSubmittedArtist(inputValue.trim());
        setInputValue('');
        setDualStep(1);
      } else {
        // Both collected — submit combined answer to backend
        const artist = submittedArtist ?? '';
        const title = inputValue.trim();
        if (!artist && !title) return;
        onSubmit(JSON.stringify({ artist, title }));
      }
    } else {
      if (!inputValue.trim()) return;
      onSubmit(inputValue.trim());
    }
  };

  const getResultStyle = () => {
    if (!showResults || !roundResults) return '';
    if (selectedAnswer && roundResults.points_earned && roundResults.points_earned > 0) {
      return 'border-green-500 bg-green-50';
    }
    return 'border-red-500 bg-red-50';
  };

  // Parse the displayed answer for dual mode
  const getDisplayAnswer = () => {
    if (!selectedAnswer) return null;
    try {
      const parsed = JSON.parse(selectedAnswer);
      if (parsed.title || parsed.artist) {
        const parts = [];
        if (parsed.artist) parts.push(`Artiste : ${parsed.artist}`);
        if (parsed.title) parts.push(`Titre : ${parsed.title}`);
        return parts.join(' • ');
      }
    } catch { /* not JSON */ }
    return selectedAnswer;
  };

  // Dual-input sequential UI (used while !hasAnswered && !showResults)
  const renderDualInput = () => (
    <div className="space-y-4">
      {/* Confirmation chips */}
      {dualStep === 1 && (
        <div className="flex justify-center">
          <span className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586 4.707 9.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z" clipRule="evenodd" />
            </svg>
            🎤 {submittedArtist ? `« ${submittedArtist} »` : 'Artiste passé'}
          </span>
        </div>
      )}

      {/* Current input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {dualStep === 0 ? '🎤 Artiste' : '🎵 Titre du morceau'}
        </label>
        <div className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
            placeholder={dualStep === 0 ? "Tapez l'artiste..." : 'Tapez le titre...'}
            className="flex-1 px-4 py-3 text-lg border-2 border-gray-300 rounded-xl
                       focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200
                       transition-all"
            autoFocus={dualStep === 0}
            maxLength={200}
          />
          <button
            onClick={handleSubmit}
            className="px-6 py-3 bg-primary-600 text-white rounded-xl font-bold text-lg
                       hover:bg-primary-700 transition shadow-lg hover:shadow-xl"
          >
            Envoyer
          </button>
        </div>
      </div>

      <p className="text-xs text-gray-400 text-center">
        {dualStep === 0
          ? "Étape 1/2 : entrez l'artiste (laissez vide si vous ne savez pas)"
          : 'Étape 2/2 : entrez le titre — Les deux corrects = double points !'}
        {' '}• Entrée pour valider
      </p>
    </div>
  );

  return (
    <div className="mb-6">
      {!hasAnswered && !showResults ? (
        dualInput ? renderDualInput() : (
          /* ── Single input (default) ── */
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">{label}</label>
            <div className="flex gap-3">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
                placeholder={placeholder}
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
              Appuyez sur Entrée pour valider • Les accents et articles sont tolérés
            </p>
          </div>
        )
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
