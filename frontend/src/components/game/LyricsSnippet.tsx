interface LyricsSnippetProps {
  snippet: string;
  correctAnswer?: string;
  showAnswer: boolean;
  className?: string;
}

/**
 * LyricsSnippet — Affiche un extrait de paroles avec un trou à combler.
 * Réutilisé par LyricsQuestion et TextModeQuestion.
 */
const LyricsSnippet = ({ snippet, correctAnswer, showAnswer, className = '' }: LyricsSnippetProps) => (
  <div className={`p-2 md:p-4 bg-gray-50 rounded-xl border-2 border-gray-200 text-center shrink-0 ${className}`}>
    <p className="text-sm md:text-lg leading-relaxed font-medium text-gray-800 italic">
      &quot;{snippet.split('_____').map((part, i, arr) => (
        <span key={i}>
          {part}
          {i < arr.length - 1 && (
            <span className="inline-block mx-1 px-3 py-1 bg-yellow-200 rounded font-bold text-yellow-800 not-italic">
              {showAnswer && correctAnswer ? correctAnswer : '???'}
            </span>
          )}
        </span>
      ))}&quot;
    </p>
  </div>
);

export default LyricsSnippet;
