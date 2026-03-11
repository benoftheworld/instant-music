import { getModeIcon, getModeLabel } from '../../constants/gameModes';
import { useGamePlayPage } from '../../hooks/pages/useGamePlayPage';
import QuizQuestion from '../../components/game/QuizQuestion';
// BlindTestInverse removed - modes consolidated into classique/rapide/generation/paroles
import YearQuestion from '../../components/game/YearQuestion';
import IntroQuestion from '../../components/game/IntroQuestion';
import LyricsQuestion from '../../components/game/LyricsQuestion';
import KaraokeQuestion from '../../components/game/KaraokeQuestion';
import GuessArtistQuestion from '../../components/game/GuessArtistQuestion';
import SlowQuestion from '../../components/game/SlowQuestion';
import TextModeQuestion from '../../components/game/TextModeQuestion';
import VolumeControl from '../../components/game/VolumeControl';
import LiveScoreboard from '../../components/game/LiveScoreboard';
import RoundLoadingScreen from '../../components/game/RoundLoadingScreen';
import RoundResultsScreen from '../../components/game/RoundResultsScreen';
import BonusActivator from '../../components/game/BonusActivator';
import PartyPlayerView from '../../components/game/PartyPlayerView';

export default function GamePlayPage() {
  const {
    roomCode,
    user,
    game,
    currentRound,
    timeRemaining,
    hasAnswered,
    selectedAnswer,
    showResults,
    roundResults,
    loading,
    myPointsEarned,
    excludedOptions,
    roundPhase,
    loadingDuration,
    dispatch,
    handleAnswerSubmit,
    handleLoadingComplete,
    handleKaraokeEnded,
    getTextPlaceholder,
    isKaraoke,
    isSolo,
    isTextMode,
    currentMode,
    commonQuestionProps,
    displayPlayers,
  } = useGamePlayPage();

  // ─── Render the correct question component based on game mode ───
  const renderQuestionComponent = () => {
    if (!currentRound || !commonQuestionProps) return null;

    if (isTextMode && currentMode !== 'generation' && currentMode !== 'karaoke') {
      return (
        <TextModeQuestion
          {...commonQuestionProps}
          placeholder={getTextPlaceholder()}
        />
      );
    }

    switch (currentMode) {
      case 'classique':
        if (game?.guess_target === 'artist') {
          return <GuessArtistQuestion {...commonQuestionProps} />;
        }
        return <QuizQuestion {...commonQuestionProps} />;
      case 'rapide':
        return <IntroQuestion {...commonQuestionProps} />;
      case 'generation':
        return <YearQuestion {...commonQuestionProps} />;
      case 'paroles':
        return <LyricsQuestion {...commonQuestionProps} />;
      case 'karaoke':
        return <KaraokeQuestion {...commonQuestionProps} onSkipSong={handleKaraokeEnded} />;
      case 'mollo':
        return <SlowQuestion {...commonQuestionProps} />;
      default:
        return <QuizQuestion {...commonQuestionProps} />;
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="min-h-screen bg-dark flex items-center justify-center">
        <div className="text-white text-2xl animate-pulse">Chargement...</div>
      </div>
    );
  }

  if (!currentRound) {
    return (
      <div className="min-h-screen bg-dark flex items-center justify-center">
        <div className="text-white text-2xl">En attente du prochain round...</div>
      </div>
    );
  }

  // Show loading screen before round starts (visible pour tous, y compris mode soirée)
  if (roundPhase === 'loading') {
    return (
      <RoundLoadingScreen
        roundNumber={currentRound.round_number}
        onComplete={handleLoadingComplete}
        duration={loadingDuration ?? game?.timer_start_round ?? 5}
      />
    );
  }

  // ── Mode Soirée : vue joueur (téléphone) ──────────────────────────────
  // Intercepte dès ici pour éviter l'affichage du classement complet (RoundResultsScreen)
  // et de l'interface complète lors des rounds. L'hôte (spectateur) continue normalement.
  if (game?.is_party_mode && user?.id !== game?.host) {
    return (
      <>
        <PartyPlayerView
          round={currentRound}
          timeRemaining={timeRemaining}
          hasAnswered={hasAnswered}
          selectedAnswer={selectedAnswer}
          showResults={roundPhase === 'results' && showResults}
          roundResults={roundResults}
          answerMode={game.answer_mode}
          onAnswerSubmit={handleAnswerSubmit}
          excludedOptions={excludedOptions}
          myPointsEarned={myPointsEarned}
        />
        {roomCode && (
          <BonusActivator
            roomCode={roomCode}
            bonusesEnabled={game?.bonuses_enabled !== false}
            players={game?.players}
            currentUserId={user?.id}
            onBonusActivated={(_bonusType, extra) => {
              if (extra.excludedOptions && extra.excludedOptions.length > 0) {
                dispatch({ type: 'SET_EXCLUDED_OPTIONS', options: extra.excludedOptions });
              }
            }}
          />
        )}
      </>
    );
  }

  // Show results screen after round ends (skip reveal phase — still showing question component)
  if (roundPhase === 'results' && roundResults) {
    return (
      <RoundResultsScreen
        round={currentRound}
        players={displayPlayers}
        correctAnswer={roundResults.correct_answer || currentRound.correct_answer || ''}
        myPointsEarned={myPointsEarned}
        myAnswer={selectedAnswer}
        playerScores={roundResults.player_scores}
        roundBonuses={roundResults.round_bonuses}
      />
    );
  }

  // Show game screen during round
  const isKaraokeLayout = isKaraoke;

  return (
    <div className="h-screen overflow-hidden flex flex-col bg-dark p-4">
      {/* Live region pour annoncer les transitions de jeu aux lecteurs d'écran */}
      <div aria-live="polite" className="sr-only">
        {roundPhase === 'playing' && currentRound &&
          `Manche ${currentRound.round_number} — ${getModeIcon(game?.mode || '')} ${getModeLabel(game?.mode || '')} — ${timeRemaining} secondes`}
        {roundPhase === 'results' && roundResults &&
          `Résultats : la bonne réponse était ${roundResults.correct_answer}`}
      </div>

      <div className={`flex-1 flex flex-col min-h-0 container mx-auto ${isKaraokeLayout ? 'max-w-7xl' : 'max-w-7xl'}`}>
        {/* Header with room code and round number */}
        <div className="flex justify-between items-center mb-2 shrink-0">
          <div className="text-white">
            <h1 className="text-xl font-bold">Partie {roomCode}</h1>
            <div className="flex items-center gap-2">
              <p className="text-sm">
                {isKaraokeLayout
                  ? `${getModeIcon(game?.mode || '')} ${getModeLabel(game?.mode || '')}`
                  : `Manche ${currentRound.round_number} — ${getModeIcon(game?.mode || '')} ${getModeLabel(game?.mode || '')}`
                }
              </p>
              {game?.answer_mode === 'text' && !isKaraokeLayout && (
                <span className="text-xs bg-amber-500/80 text-white px-2 py-0.5 rounded-full font-medium">
                  ⌨️ Saisie libre
                </span>
              )}
            </div>
          </div>

          {/* Timer — hidden for karaoke */}
          {!isKaraoke && (
            <div className="flex items-center gap-3">
              <VolumeControl variant="floating" />
              {roundPhase === 'reveal' ? (
                <div className="text-4xl font-bold text-green-400">
                  ✓
                </div>
              ) : (
                <div
                  className={`text-6xl font-bold ${
                    timeRemaining <= 5 ? 'text-red-400 animate-pulse' : 'text-white'
                  }`}
                  role="timer"
                  aria-label={`${timeRemaining} secondes restantes`}
                >
                  {timeRemaining}s
                </div>
              )}
              {/* Annonces screen reader aux seuils critiques */}
              <div aria-live="assertive" className="sr-only">
                {timeRemaining === 10 && '10 secondes restantes'}
                {timeRemaining === 5 && '5 secondes restantes'}
              </div>
            </div>
          )}
          {isKaraoke && (
            <div className="flex items-center gap-3">
              <VolumeControl variant="floating" />
            </div>
          )}
        </div>

        {isKaraoke ? (
          /* Karaoke: full-width layout, no scoreboard */
          <div className="flex-1 min-h-0 overflow-y-auto">
            {renderQuestionComponent()}
          </div>
        ) : (
          <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
            {/* Main quiz area */}
            <div className="lg:col-span-2 overflow-hidden min-h-0 flex flex-col">
              {renderQuestionComponent()}
            </div>
            {/* Live scoreboard — hidden on mobile to free space for MCQ options */}
            <div className="hidden lg:block lg:col-span-1 overflow-y-auto min-h-0">
              <LiveScoreboard players={game?.players || []} />
            </div>
          </div>
        )}
      </div>
      {/* Panneau d'activation des bonus — flottant en bas à droite */}
      {roomCode && !isSolo && (
        <BonusActivator
          roomCode={roomCode}
          bonusesEnabled={game?.bonuses_enabled !== false}
          players={game?.players}
          currentUserId={user?.id}
          onBonusActivated={(_bonusType, extra) => {
            if (extra.excludedOptions && extra.excludedOptions.length > 0) {
              dispatch({ type: 'SET_EXCLUDED_OPTIONS', options: extra.excludedOptions });
            }
            // new_duration is handled via the bonus_activated WS event
          }}
        />
      )}
    </div>
  );
}
