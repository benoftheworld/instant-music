import type { GameMode, AnswerMode, GuessTarget } from '../../../types';
import { gameModes } from './gameModes';

interface Props {
  selectedMode: GameMode;
  answerMode: AnswerMode;
  setAnswerMode: (m: AnswerMode) => void;
  guessTarget: GuessTarget;
  setGuessTarget: (t: GuessTarget) => void;
  onSelectMode: (m: GameMode) => void;
}

export default function StepMode({ selectedMode, answerMode, setAnswerMode, guessTarget, setGuessTarget, onSelectMode }: Props) {
  return (
    <div className="space-y-6">
      {/* Mode selection */}
      <div className="card">
        <h3 className="text-lg font-bold mb-4 bg-[#C42F38] text-white text-center py-2 px-3 rounded">Choisissez un mode</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {gameModes.map((mode) => {
            const isSelected = selectedMode === mode.value;
            return (
              <button
                key={mode.value}
                onClick={() => onSelectMode(mode.value)}
                className={`p-5 rounded-xl border-2 text-left transition-all relative ${
                  isSelected
                    ? 'border-primary-600 bg-primary-50 shadow-md'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                {isSelected && (
                  <span className="absolute top-3 right-3 text-primary-600">
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </span>
                )}
                <div className="text-3xl mb-2">{mode.icon}</div>
                <h4 className="font-bold text-lg mb-1">{mode.label}</h4>
                <p className="text-sm text-gray-600">{mode.description}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Mode-specific config */}
      <div className="card">
        <h3 className="text-lg font-bold mb-4 bg-[#C42F38] text-white text-center py-2 px-3 rounded">Configuration du mode</h3>
        {selectedMode === 'karaoke' && (
          <div className="mb-4 p-3 bg-pink-100 border border-pink-200 rounded text-center">
            <p className="text-sm text-pink-800 font-semibold">Le mode <strong>Karaoké</strong> n'a pas de configuration spécifique ici — il se joue en solo et les paramètres sont automatiques.</p>
          </div>
        )}

        {/* Answer mode — hidden for karaoke */}
        {selectedMode !== 'karaoke' && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Mode de réponse
            </label>
            <div className="flex gap-3">
              <button
                onClick={() => setAnswerMode('mcq')}
                className={`flex-1 p-4 rounded-lg border-2 text-center transition-all ${
                  answerMode === 'mcq'
                    ? 'border-primary-600 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                <div className="text-2xl mb-1">🔘</div>
                <div className="font-semibold text-sm">QCM</div>
                <p className="text-xs text-gray-500 mt-1">4 réponses proposées</p>
              </button>
              <button
                onClick={() => setAnswerMode('text')}
                className={`flex-1 p-4 rounded-lg border-2 text-center transition-all ${
                  answerMode === 'text'
                    ? 'border-primary-600 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                <div className="text-2xl mb-1">⌨️</div>
                <div className="font-semibold text-sm">Saisie libre</div>
                <p className="text-xs text-gray-500 mt-1">Écrire la réponse</p>
              </button>
            </div>
          </div>
        )}

        {/* Classique / Rapide / Mollo specific */}
        {(selectedMode === 'classique' || selectedMode === 'rapide' || selectedMode === 'mollo') && (
          <div className="space-y-4">
            {answerMode === 'mcq' ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Que doit trouver le joueur ?
                </label>
                <div className="flex gap-3">
                  <button
                    onClick={() => setGuessTarget('title')}
                    className={`flex-1 p-3 rounded-lg border-2 text-center transition-all ${
                      guessTarget === 'title'
                        ? 'border-primary-600 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300 bg-white'
                    }`}
                  >
                    <div className="text-xl mb-1">🎵</div>
                    <div className="font-semibold text-sm">Le titre</div>
                  </button>
                  <button
                    onClick={() => setGuessTarget('artist')}
                    className={`flex-1 p-3 rounded-lg border-2 text-center transition-all ${
                      guessTarget === 'artist'
                        ? 'border-primary-600 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300 bg-white'
                    }`}
                  >
                    <div className="text-xl mb-1">🎤</div>
                    <div className="font-semibold text-sm">L'artiste</div>
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-sm text-amber-800">
                  <strong>💡 Saisie libre :</strong> Le joueur peut tenter de trouver l'artiste <strong>et/ou</strong> le titre.
                  S'il trouve les deux, il <strong>double ses points</strong> !
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
