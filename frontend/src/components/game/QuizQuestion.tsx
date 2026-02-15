interface Round {
  id: string;
  round_number: number;
  track_id: string;
  track_name: string;
  artist_name: string;
  options: string[];
  duration: number;
  started_at: string;
  ended_at: string | null;
}

interface RoundResults {
  correct_answer: string;
  points_earned?: number;
}

interface QuizQuestionProps {
  round: Round;
  onAnswerSubmit: (answer: string) => void;
  hasAnswered: boolean;
  selectedAnswer: string | null;
  showResults: boolean;
  roundResults: RoundResults | null;
}

const QuizQuestion = ({
  round,
  onAnswerSubmit,
  hasAnswered,
  selectedAnswer,
  showResults,
  roundResults,
}: QuizQuestionProps) => {
  const handleOptionClick = (option: string) => {
    if (!hasAnswered && !showResults) {
      onAnswerSubmit(option);
    }
  };
  
  const getOptionStyle = (option: string) => {
    // Before answering
    if (!hasAnswered && !showResults) {
      return 'bg-white hover:bg-blue-100 border-2 border-gray-300 hover:border-blue-500 cursor-pointer';
    }
    
    // After answering but before results
    if (hasAnswered && !showResults) {
      if (option === selectedAnswer) {
        return 'bg-blue-500 text-white border-2 border-blue-700';
      }
      return 'bg-gray-200 border-2 border-gray-300 cursor-not-allowed';
    }
    
    // Show results
    if (showResults && roundResults) {
      const isCorrect = option === roundResults.correct_answer;
      const isSelected = option === selectedAnswer;
      
      if (isCorrect) {
        return 'bg-green-500 text-white border-2 border-green-700';
      }
      if (isSelected && !isCorrect) {
        return 'bg-red-500 text-white border-2 border-red-700';
      }
      return 'bg-gray-200 border-2 border-gray-300';
    }
    
    return 'bg-white border-2 border-gray-300';
  };
  
  return (
    <div className="bg-white rounded-lg shadow-xl p-8">
      {/* Question header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Quel est le titre de ce morceau ?
        </h2>
        <p className="text-gray-600">
          Artiste : <span className="font-semibold">{round.artist_name}</span>
        </p>
      </div>
      
      {/* Audio player (if preview available) */}
      {/* TODO: Add audio preview when available */}
      
      {/* Answer options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {round.options.map((option, index) => (
          <button
            key={index}
            onClick={() => handleOptionClick(option)}
            className={`p-4 rounded-lg text-left transition-all duration-200 ${getOptionStyle(option)}`}
            disabled={hasAnswered || showResults}
          >
            <div className="flex items-center">
              <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center mr-3 font-bold">
                {String.fromCharCode(65 + index)}
              </div>
              <span className="text-lg font-medium">{option}</span>
            </div>
          </button>
        ))}
      </div>
      
      {/* Status message */}
      {hasAnswered && !showResults && (
        <div className="text-center text-lg text-gray-600 animate-pulse">
          En attente des autres joueurs...
        </div>
      )}
      
      {/* Results */}
      {showResults && roundResults && (
        <div className="mt-6 p-4 rounded-lg bg-blue-50 border-2 border-blue-200">
          <p className="text-lg">
            <span className="font-bold">Bonne réponse:</span> {roundResults.correct_answer}
          </p>
          {selectedAnswer === roundResults.correct_answer ? (
            <p className="text-green-600 font-bold mt-2">
              ✓ Bravo ! Vous avez gagné {roundResults.points_earned || 0} points
            </p>
          ) : (
            <p className="text-red-600 font-bold mt-2">
              ✗ Dommage ! C'était "{roundResults.correct_answer}"
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default QuizQuestion;
