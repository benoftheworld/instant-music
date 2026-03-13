import type { RoundResults } from './types';

export function ResultFooter({
  showResults,
  roundResults,
  selectedAnswer,
  hasAnswered,
}: {
  showResults: boolean;
  roundResults: RoundResults | null;
  selectedAnswer: string | null;
  hasAnswered: boolean;
}) {
  return (
    <>
      {hasAnswered && !showResults && (
        <div className="text-center text-sm text-gray-600 animate-pulse mt-2 shrink-0">
          En attente des autres joueurs...
        </div>
      )}
      {showResults && roundResults && (
        <div className="mt-3 p-3 rounded-lg bg-primary-50 border-2 border-primary-200 shrink-0">
          <p className="text-base">
            <span className="font-bold">Bonne réponse :</span> {roundResults.correct_answer}
          </p>
          {selectedAnswer === roundResults.correct_answer ? (
            <p className="text-green-600 font-bold mt-1">
              ✓ Bravo ! +{roundResults.points_earned || 0} points
            </p>
          ) : (
            <p className="text-red-600 font-bold mt-1">
              ✗ Dommage ! C&apos;était &quot;{roundResults.correct_answer}&quot;
            </p>
          )}
        </div>
      )}
    </>
  );
}
