/**
 * PartyPlayerView — vue simplifiée pour les joueurs en Mode Soirée.
 *
 * L'hôte projette l'interface complète sur grand écran.
 * Les joueurs voient uniquement les boutons de réponse (QCM ou saisie libre)
 * sur leur téléphone — sans musique, sans informations sur le morceau.
 */

import { useState, useRef, useEffect } from 'react';
import type { GameRound } from '../../types';
import type { RoundResults } from '../../hooks/useGamePlayReducer';

// Couleurs Kahoot-style pour les 4 options QCM
const OPTION_STYLES = [
  { bg: 'bg-red-500 hover:bg-red-600 active:bg-red-700', border: 'border-red-600', icon: '▲' },
  { bg: 'bg-blue-500 hover:bg-blue-600 active:bg-blue-700', border: 'border-blue-600', icon: '◆' },
  { bg: 'bg-yellow-400 hover:bg-yellow-500 active:bg-yellow-600', border: 'border-yellow-500', icon: '●' },
  { bg: 'bg-green-500 hover:bg-green-600 active:bg-green-700', border: 'border-green-600', icon: '■' },
];

interface PartyPlayerViewProps {
  round: GameRound;
  timeRemaining: number;
  hasAnswered: boolean;
  selectedAnswer: string | null;
  showResults: boolean;
  roundResults: RoundResults | null;
  answerMode: 'mcq' | 'text';
  onAnswerSubmit: (answer: string) => void;
  excludedOptions?: string[];
  myPointsEarned?: number;
}

export default function PartyPlayerView({
  round,
  timeRemaining,
  hasAnswered,
  selectedAnswer,
  showResults,
  roundResults,
  answerMode,
  onAnswerSubmit,
  excludedOptions = [],
  myPointsEarned = 0,
}: PartyPlayerViewProps) {
  const [textAnswer, setTextAnswer] = useState('');
  const [prevRoundNumber, setPrevRoundNumber] = useState(round.round_number);
  const inputRef = useRef<HTMLInputElement>(null);

  // Réinitialiser l'input texte à chaque nouveau round
  if (prevRoundNumber !== round.round_number) {
    setPrevRoundNumber(round.round_number);
    setTextAnswer('');
  }

  // Toujours focus l'input en mode texte
  useEffect(() => {
    if (answerMode === 'text' && !hasAnswered && inputRef.current) {
      inputRef.current.focus();
    }
  }, [answerMode, hasAnswered]);

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = textAnswer.trim();
    if (!trimmed || hasAnswered) return;
    onAnswerSubmit(trimmed);
  };

  // ── Affichage résultats ────────────────────────────────────────────────
  if (showResults) {
    const isCorrect =
      selectedAnswer !== null &&
      roundResults?.correct_answer !== undefined &&
      selectedAnswer.toLowerCase().trim() === roundResults.correct_answer.toLowerCase().trim();

    return (
      <div className="h-screen flex flex-col items-center justify-center bg-dark p-6 gap-6">
        <div className={`w-full max-w-sm rounded-2xl p-8 text-center shadow-2xl ${
          isCorrect ? 'bg-green-500' : selectedAnswer ? 'bg-red-500' : 'bg-gray-600'
        }`}>
          <div className="text-6xl mb-4">
            {isCorrect ? '✅' : selectedAnswer ? '❌' : '⏱️'}
          </div>
          <p className="text-white text-2xl font-bold mb-2">
            {isCorrect ? 'Bonne réponse !' : selectedAnswer ? 'Mauvaise réponse' : 'Temps écoulé'}
          </p>
          {isCorrect && myPointsEarned > 0 && (
            <p className="text-white/90 text-xl font-semibold">+{myPointsEarned} pts</p>
          )}
          {roundResults?.correct_answer && !isCorrect && (
            <p className="text-white/80 text-sm mt-3">
              Réponse :{' '}
              <span className="font-bold">{roundResults.correct_answer}</span>
            </p>
          )}
        </div>
        <p className="text-white/60 text-sm">En attente de la prochaine manche…</p>
      </div>
    );
  }

  // ── Réponse déjà envoyée ──────────────────────────────────────────────
  if (hasAnswered) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-dark p-6 gap-6">
        <div className="w-full max-w-sm rounded-2xl p-8 text-center bg-white/10 border-2 border-white/20 shadow-2xl">
          <div className="text-5xl mb-4">✔️</div>
          <p className="text-white text-xl font-bold mb-2">Réponse envoyée !</p>
          {selectedAnswer && (
            <p className="text-white/70 text-sm">
              Votre réponse : <span className="font-semibold text-white/90">« {selectedAnswer} »</span>
            </p>
          )}
          <p className="text-white/50 text-xs mt-4">En attente des autres joueurs…</p>
        </div>
        {/* Timer réduit */}
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${timeRemaining <= 5 ? 'bg-red-400 animate-pulse' : 'bg-green-400'}`} />
          <span className={`font-mono font-bold text-xl ${timeRemaining <= 5 ? 'text-red-300' : 'text-white/80'}`}>
            {timeRemaining}s
          </span>
        </div>
      </div>
    );
  }

  // ── Timer + indicateur de manche ─────────────────────────────────────
  const timerPercent = Math.min(100, (timeRemaining / round.duration) * 100);
  const timerColor =
    timerPercent > 50 ? 'bg-green-400' : timerPercent > 20 ? 'bg-yellow-400' : 'bg-red-500';

  const availableOptions = round.options.filter((opt) => !excludedOptions.includes(opt));

  // ── Mode QCM ──────────────────────────────────────────────────────────
  if (answerMode === 'mcq') {
    return (
      <div className="h-screen flex flex-col bg-dark p-4 gap-3 overflow-hidden">
        {/* Header : round + timer */}
        <div className="flex items-center justify-between px-2 shrink-0">
          <span className="text-white/70 text-sm font-semibold uppercase tracking-widest">
            Manche {round.round_number}
          </span>
          <span className={`font-mono text-2xl font-bold ${timeRemaining <= 5 ? 'text-red-300 animate-pulse' : 'text-white'}`}>
            {timeRemaining}
          </span>
        </div>

        {/* Barre de progression */}
        <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden shrink-0">
          <div
            className={`h-full rounded-full transition-all duration-500 ${timerColor}`}
            style={{ width: `${timerPercent}%` }}
          />
        </div>

        {/* Boutons de réponse en grille 2×2 */}
        <div className="flex-1 min-h-0 grid grid-cols-2 gap-3">
          {availableOptions.map((option, idx) => {
            const style = OPTION_STYLES[idx % OPTION_STYLES.length];
            return (
              <button
                key={option}
                onClick={() => onAnswerSubmit(option)}
                className={`
                  ${style.bg} text-white font-bold text-base
                  rounded-2xl shadow-lg border-b-4 ${style.border}
                  flex flex-col items-center justify-center gap-1
                  transition-transform active:scale-95 active:border-b-0 active:translate-y-1
                  p-3 min-h-0 overflow-hidden
                `}
              >
                <span className="text-xl opacity-80 shrink-0">{style.icon}</span>
                <span className="text-center leading-tight line-clamp-3 text-sm">{option}</span>
              </button>
            );
          })}
          {/* Placeholders si 50/50 a été utilisé */}
          {Array.from({ length: Math.max(0, 4 - availableOptions.length) }).map((_, i) => (
            <div
              key={`placeholder-${i}`}
              className="bg-white/10 rounded-2xl border-2 border-dashed border-white/20"
            />
          ))}
        </div>
      </div>
    );
  }

  // ── Mode saisie libre ─────────────────────────────────────────────────
  return (
    <div className="h-screen flex flex-col bg-dark p-4 gap-4">
      {/* Header */}
      <div className="flex items-center justify-between px-2">
        <span className="text-white/70 text-sm font-semibold uppercase tracking-widest">
          Manche {round.round_number}
        </span>
        <span className={`font-mono text-2xl font-bold ${timeRemaining <= 5 ? 'text-red-300 animate-pulse' : 'text-white'}`}>
          {timeRemaining}
        </span>
      </div>

      {/* Barre de progression */}
      <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${timerColor}`}
          style={{ width: `${timerPercent}%` }}
        />
      </div>

      {/* Zone de saisie */}
      <div className="flex-1 flex flex-col items-center justify-center gap-6 px-2">
        <p className="text-white/80 text-lg font-semibold text-center">
          {round.question_type === 'guess_artist'
            ? "Quel est l'artiste ?"
            : round.question_type === 'lyrics'
            ? 'Quel est le mot manquant ?'
            : 'Quel est le titre ?'}
        </p>
        <form onSubmit={handleTextSubmit} className="w-full max-w-sm flex flex-col gap-4">
          <input
            ref={inputRef}
            type="text"
            value={textAnswer}
            onChange={(e) => setTextAnswer(e.target.value)}
            placeholder="Votre réponse…"
            autoComplete="off"
            autoCorrect="off"
            className="w-full px-5 py-4 text-lg rounded-2xl border-2 border-white/30 bg-white/10
                       text-white placeholder-white/40 focus:outline-none focus:border-white/70
                       focus:bg-white/20 transition-all"
          />
          <button
            type="submit"
            disabled={!textAnswer.trim()}
            className="w-full py-4 text-lg font-bold rounded-2xl bg-primary-500 hover:bg-primary-600
                       active:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed
                       text-white shadow-lg border-b-4 border-primary-700 transition-all
                       active:scale-95 active:border-b-0 active:translate-y-1"
          >
            Valider
          </button>
        </form>
      </div>
    </div>
  );
}
