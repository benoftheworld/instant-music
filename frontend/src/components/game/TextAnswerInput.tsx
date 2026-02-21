import { useState } from 'react';

interface TextAnswerInputProps {
  onSubmit: (answer: string) => void;
  hasAnswered: boolean;
  selectedAnswer: string | null;
  showResults: boolean;
  roundResults: { correct_answer: string; points_earned?: number } | null;
  placeholder?: string;
  label?: string;
  /** When true, shows two fields (title + artist) for Classique/Rapide text mode */
  dualInput?: boolean;
}

/**
 * TextAnswerInput – Free-text input for text answer mode.
 * Used instead of MCQ options when game.answer_mode === 'text'.
 * In dualInput mode, shows separate Title and Artist fields and submits JSON.
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
  const [titleValue, setTitleValue] = useState('');
  const [artistValue, setArtistValue] = useState('');
  const [submittedBoth, setSubmittedBoth] = useState(false);

  const handleSubmit = () => {
    if (hasAnswered) return;

    if (dualInput) {
      const title = titleValue.trim();
      const artist = artistValue.trim();
      if (!title && !artist) return;
      const answer = JSON.stringify({ artist, title });
      setSubmittedBoth(!!title && !!artist);
      onSubmit(answer);
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
        if (parsed.title) parts.push(`Titre : ${parsed.title}`);
        if (parsed.artist) parts.push(`Artiste : ${parsed.artist}`);
        return parts.join(' • ');
      }
    } catch { /* not JSON */ }
    return selectedAnswer;
  };

  return (
    <div className="mb-6">
      {!hasAnswered && !showResults ? (
        dualInput ? (
          /* ── Dual input: Title + Artist ── */
          <div className="space-y-4">
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">🎵 Titre du morceau</label>
                <input
                  type="text"
                  value={titleValue}
                  onChange={(e) => setTitleValue(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
                  placeholder="Tapez le titre..."
                  className="w-full px-4 py-3 text-lg border-2 border-gray-300 rounded-xl
                             focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200
                             transition-all"
                  autoFocus
                  maxLength={200}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">🎤 Artiste</label>
                <input
                  type="text"
                  value={artistValue}
                  onChange={(e) => setArtistValue(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
                  placeholder="Tapez l'artiste..."
                  className="w-full px-4 py-3 text-lg border-2 border-gray-300 rounded-xl
                             focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200
                             transition-all"
                  maxLength={200}
                />
              </div>
            </div>
            <div className="flex justify-center">
              <button
                onClick={handleSubmit}
                disabled={!titleValue.trim() && !artistValue.trim()}
                className="px-8 py-3 bg-primary-600 text-white rounded-xl font-bold text-lg
                           hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed
                           shadow-lg hover:shadow-xl"
              >
                Valider
              </button>
            </div>
            <p className="text-xs text-gray-400 text-center">
              Remplissez titre et/ou artiste • Les deux corrects = double points ! • Entrée pour valider
            </p>
          </div>
        ) : (
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
          {dualInput && submittedBoth && (
            <div className="text-xs text-amber-600 mt-1">
              ✨ Titre + Artiste soumis — chance de double points !
            </div>
          )}
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
