import { useCreateGamePage } from '../../hooks/pages/useCreateGamePage';
import StepMode from './create-game/StepMode';
import StepConfig from './create-game/StepConfig';
import StepPlaylist from './create-game/StepPlaylist';
import StepConfirm from './create-game/StepConfirm';

export default function CreateGamePage() {
  const {
    navigate,
    loading,
    error,
    currentStep,
    setCurrentStep,
    selectedMode,
    answerMode,
    setAnswerMode,
    guessTarget,
    setGuessTarget,
    lyricsWordsCount,
    setLyricsWordsCount,
    roundDuration,
    setRoundDuration,
    scoreDisplayDuration,
    setScoreDisplayDuration,
    maxPlayers,
    setMaxPlayers,
    numRounds,
    setNumRounds,
    isOnline,
    isPublic,
    setIsPublic,
    isPartyMode,
    setIsPartyMode,
    isBonusesEnabled,
    setIsBonusesEnabled,
    selectedPlaylist,
    karaokeSelectedSong,
    isKaraoke,
    LAST_STEP,
    nextStep,
    prevStep,
    canProceed,
    handleCreateGame,
    handleSelectMode,
    handleToggleOffline,
    handleSelectPlaylist,
    handleSelectKaraokeSong,
  } = useCreateGamePage();

  const visibleSteps = isKaraoke ? [1, 3, 4] : [1, 2, 3, 4];
  const activeIndex = visibleSteps.indexOf(currentStep);

  const stepTitles: Record<number, string> = {
    1: 'Mode de jeu',
    2: 'Configuration globale',
    3: isKaraoke ? 'Sélection du morceau' : 'Sélection de la playlist',
    4: 'Confirmation',
  };
  const stepSubtitles: Record<number, string> = {
    1: 'Choisissez votre mode de jeu et ses options',
    2: 'Paramétrez les timers, le nombre de joueurs et les options générales',
    3: isKaraoke
      ? 'Choisissez un morceau dans le catalogue karaoké'
      : 'Choisissez la playlist musicale pour la partie',
    4: 'Vérifiez vos choix et lancez la partie',
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-900 mb-4 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Retour
          </button>
          <h1 className="text-4xl font-bold">Créer une partie</h1>
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-center mb-8">
          {visibleSteps.map((step, idx) => (
            <div key={step} className="flex items-center">
              <button
                onClick={() => activeIndex > idx && setCurrentStep(step)}
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all ${
                  step === currentStep
                    ? 'bg-primary-600 text-white shadow-lg scale-110'
                    : activeIndex > idx
                    ? 'bg-primary-200 text-primary-700 cursor-pointer hover:bg-primary-300'
                    : 'bg-gray-200 text-gray-400'
                }`}
              >
                {activeIndex > idx ? '✓' : idx + 1}
              </button>
              {idx < visibleSteps.length - 1 && (
                <div
                  className={`w-16 h-1 mx-1 rounded ${
                    activeIndex > idx ? 'bg-primary-400' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step title */}
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold">{stepTitles[currentStep]}</h2>
          <p className="text-gray-600 text-sm mt-1">{stepSubtitles[currentStep]}</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {/* Step content */}
        {currentStep === 1 && (
          <StepMode
            selectedMode={selectedMode}
            answerMode={answerMode}
            setAnswerMode={setAnswerMode}
            guessTarget={guessTarget}
            setGuessTarget={setGuessTarget}
            onSelectMode={handleSelectMode}
          />
        )}
        {currentStep === 2 && (
          <StepConfig
            selectedMode={selectedMode}
            isKaraoke={isKaraoke}
            isOnline={isOnline}
            isPublic={isPublic}
            setIsPublic={setIsPublic}
            isPartyMode={isPartyMode}
            setIsPartyMode={setIsPartyMode}
            isBonusesEnabled={isBonusesEnabled}
            setIsBonusesEnabled={setIsBonusesEnabled}
            roundDuration={roundDuration}
            setRoundDuration={setRoundDuration}
            scoreDisplayDuration={scoreDisplayDuration}
            setScoreDisplayDuration={setScoreDisplayDuration}
            lyricsWordsCount={lyricsWordsCount}
            setLyricsWordsCount={setLyricsWordsCount}
            maxPlayers={maxPlayers}
            setMaxPlayers={setMaxPlayers}
            numRounds={numRounds}
            setNumRounds={setNumRounds}
            handleToggleOffline={handleToggleOffline}
          />
        )}
        {currentStep === 3 && (
          <StepPlaylist
            isKaraoke={isKaraoke}
            selectedPlaylist={selectedPlaylist}
            karaokeSelectedSong={karaokeSelectedSong}
            onSelectPlaylist={handleSelectPlaylist}
            onSelectKaraokeSong={handleSelectKaraokeSong}
          />
        )}
        {currentStep === 4 && (
          <StepConfirm
            isKaraoke={isKaraoke}
            isOnline={isOnline}
            isPublic={isPublic}
            isPartyMode={isPartyMode}
            isBonusesEnabled={isBonusesEnabled}
            selectedMode={selectedMode}
            answerMode={answerMode}
            guessTarget={guessTarget}
            lyricsWordsCount={lyricsWordsCount}
            roundDuration={roundDuration}
            scoreDisplayDuration={scoreDisplayDuration}
            maxPlayers={maxPlayers}
            numRounds={numRounds}
            selectedPlaylist={selectedPlaylist}
            karaokeSelectedSong={karaokeSelectedSong}
          />
        )}

        {/* Navigation buttons */}
        <div className="card mt-6">
          <div className="flex gap-4">
            {currentStep === 1 ? (
              <button onClick={() => navigate('/')} className="btn-secondary flex-1">
                Annuler
              </button>
            ) : (
              <button onClick={prevStep} className="btn-secondary flex-1">
                ← Précédent
              </button>
            )}

            {currentStep < LAST_STEP ? (
              <button
                onClick={nextStep}
                className="btn-primary flex-1"
                disabled={!canProceed()}
              >
                Suivant →
              </button>
            ) : (
              <button
                onClick={handleCreateGame}
                className="btn-primary flex-1"
                disabled={loading || (isKaraoke ? !karaokeSelectedSong : !selectedPlaylist)}
              >
                {loading ? 'Création...' : 'Créer la partie'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
