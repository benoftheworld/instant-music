import {
  useAudioPlayer, AudioPlayerUI, OptionsGrid, ResultFooter, TrackReveal,
  type Props,
} from './shared';

/**
 * BlindTestInverse – The artist is given prominently.
 * Player must guess the correct song title from 4 options.
 */
const BlindTestInverse = ({
  round,
  onAnswerSubmit,
  hasAnswered,
  selectedAnswer,
  showResults,
  roundResults,
}: Props) => {
  const audio = useAudioPlayer(round, showResults);

  return (
    <div className="bg-white rounded-lg shadow-xl p-8">
      {/* Prominent artist display */}
      <div className="mb-6 text-center">
        <div className="inline-block bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-6 py-3 rounded-full text-lg font-bold mb-3 shadow-lg">
          🎤 {round.artist_name}
        </div>
        <h2 className="text-2xl font-bold text-gray-800">
          {round.question_text || 'Quel est le titre de ce morceau ?'}
        </h2>
      </div>

      {!showResults && (
        <div className="mb-6">
          <AudioPlayerUI {...audio} />
        </div>
      )}

      {showResults && <TrackReveal round={round} />}

      <OptionsGrid
        options={round.options}
        hasAnswered={hasAnswered}
        showResults={showResults}
        selectedAnswer={selectedAnswer}
        roundResults={roundResults}
        onOptionClick={onAnswerSubmit}
      />

      <ResultFooter
        showResults={showResults}
        roundResults={roundResults}
        selectedAnswer={selectedAnswer}
        hasAnswered={hasAnswered}
      />
    </div>
  );
};

export default BlindTestInverse;
