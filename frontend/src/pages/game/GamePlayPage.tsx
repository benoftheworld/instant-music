import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { gameService } from '../../services/gameService';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useAuthStore } from '../../store/authStore';
import QuizQuestion from '../../components/game/QuizQuestion';
import BlindTestInverse from '../../components/game/BlindTestInverse';
import YearQuestion from '../../components/game/YearQuestion';
import IntroQuestion from '../../components/game/IntroQuestion';
import LyricsQuestion from '../../components/game/LyricsQuestion';
import GuessArtistQuestion from '../../components/game/GuessArtistQuestion';
import LiveScoreboard from '../../components/game/LiveScoreboard';
import RoundLoadingScreen from '../../components/game/RoundLoadingScreen';
import RoundResultsScreen from '../../components/game/RoundResultsScreen';

interface Round {
  id: string;
  round_number: number;
  track_id: string;
  track_name: string;
  artist_name: string;
  preview_url?: string;
  options: string[];
  question_type: string;
  question_text: string;
  extra_data: Record<string, any>;
  duration: number;
  started_at: string;
  ended_at: string | null;
  correct_answer?: string;
}

export default function GamePlayPage() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  
  const [game, setGame] = useState<any>(null);
  const [currentRound, setCurrentRound] = useState<Round | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const [hasAnswered, setHasAnswered] = useState(false);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [roundResults, setRoundResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [myPointsEarned, setMyPointsEarned] = useState<number>(0);
  const isAdvancingRef = useRef(false);
  
  // New state for round phases: 'loading' | 'playing' | 'results'
  const [roundPhase, setRoundPhase] = useState<'loading' | 'playing' | 'results'>('loading');
  const loadingStartTimeRef = useRef<number>(0);
  
  // WebSocket connection
  const { sendMessage, onMessage } = useWebSocket(roomCode || '');
  
  // Load current round
  const loadCurrentRound = useCallback(async () => {
    if (!roomCode) return;
    
    try {
      const response = await gameService.getCurrentRound(roomCode);
      
      if (response.current_round) {
        setCurrentRound(response.current_round);
        setTimeRemaining(response.current_round.duration);
        setHasAnswered(false);
        setSelectedAnswer(null);
        setShowResults(false);
        setRoundPhase('loading'); // Start with loading phase
        loadingStartTimeRef.current = Date.now(); // Record when loading starts
      } else if (response.message === 'Partie terminée') {
        // Game is finished
        navigate(`/game/${roomCode}/results`);
      }
    } catch (error) {
      console.error('Failed to load round:', error);
    } finally {
      setLoading(false);
    }
  }, [roomCode, navigate]);
  
  // Load game data
  const loadGame = useCallback(async () => {
    if (!roomCode) return;
    
    try {
      const gameData = await gameService.getGame(roomCode);
      setGame(gameData);
      
      if (gameData.status === 'finished') {
        navigate(`/game/${roomCode}/results`);
      }
    } catch (error) {
      console.error('Failed to load game:', error);
    }
  }, [roomCode, navigate]);
  
  // Advance to next round (guarded against double calls)
  const advanceToNextRound = useCallback(async () => {
    if (isAdvancingRef.current || !roomCode) return;
    isAdvancingRef.current = true;
    try {
      await gameService.nextRound(roomCode);
    } catch (error) {
      console.error('Failed to advance to next round:', error);
    } finally {
      // Reset after a delay to prevent rapid re-triggers
      setTimeout(() => { isAdvancingRef.current = false; }, 3000);
    }
  }, [roomCode]);

  // Timer countdown - calculate based on server time
  useEffect(() => {
    if (!currentRound || showResults || roundPhase !== 'playing') return;
    
    const calculateTimeRemaining = () => {
      if (!currentRound.started_at) return currentRound.duration;
      const startTime = new Date(currentRound.started_at).getTime();
      const now = Date.now();
      
      // Compensate for the 10 seconds loading screen
      const loadingDuration = loadingStartTimeRef.current > 0 ? 10000 : 0; // 10 seconds in ms
      const adjustedStartTime = startTime + loadingDuration;
      
      const elapsed = Math.floor((now - adjustedStartTime) / 1000);
      const remaining = Math.max(0, currentRound.duration - elapsed);
      return remaining;
    };
    
    // Update immediately
    const remaining = calculateTimeRemaining();
    setTimeRemaining(remaining);
    
    let timerTimeout: ReturnType<typeof setTimeout> | null = null;
    
    // Update every 100ms for smooth countdown
    const interval = setInterval(() => {
      const newRemaining = calculateTimeRemaining();
      setTimeRemaining(newRemaining);
      
      if (newRemaining <= 0) {
        clearInterval(interval);
        
        // If timer reaches 0 and user is host, trigger next round after delay
        if (user && game && game.host === user.id) {
          timerTimeout = setTimeout(() => {
            advanceToNextRound();
          }, 2000);
        }
      }
    }, 100);
    
    return () => {
      clearInterval(interval);
      if (timerTimeout) clearTimeout(timerTimeout);
    };
  }, [currentRound, showResults, roundPhase, game, roomCode, user, advanceToNextRound]);
  
  // Handle WebSocket messages
  useEffect(() => {
    const unsubscribe = onMessage('message', (data: any) => {
      console.log('WebSocket message:', data);
      
      switch (data.type) {
        case 'round_started':
          // New round started
          setCurrentRound(data.round_data);
          setTimeRemaining(data.round_data.duration);
          setHasAnswered(false);
          setSelectedAnswer(null);
          setShowResults(false);
          setRoundPhase('loading'); // Show loading screen first
          loadingStartTimeRef.current = Date.now(); // Record when loading starts
          break;
          
        case 'player_answered':
          // Another player answered
          console.log('Player answered:', data.player);
          break;
          
        case 'round_ended':
          // Round finished, show results
          setShowResults(true);
          setRoundPhase('results'); // Show results screen
          setRoundResults({
            ...data.results,
            points_earned: data.results?.player_scores?.[user?.username || '']?.points_earned ?? myPointsEarned,
          });
          // Update players with fresh scores from backend (functional update to avoid stale closure)
          if (data.results?.updated_players) {
            setGame((prev: any) => prev ? { ...prev, players: data.results.updated_players } : prev);
          }
          break;
          
        case 'next_round':
          // Move to next round automatically
          isAdvancingRef.current = false;
          setCurrentRound(data.round_data);
          setTimeRemaining(data.round_data.duration);
          setHasAnswered(false);
          setSelectedAnswer(null);
          setShowResults(false);
          setRoundResults(null);
          setMyPointsEarned(0);
          setRoundPhase('loading'); // Show loading screen for new round
          loadingStartTimeRef.current = Date.now(); // Record when loading starts
          // Update players with fresh scores (functional update to avoid stale closure)
          if (data.updated_players) {
            setGame((prev: any) => prev ? { ...prev, players: data.updated_players } : prev);
          }
          break;
          
        case 'game_finished':
          // Game over
          navigate(`/game/${roomCode}/results`);
          break;
      }
    });
    
    return unsubscribe;
  }, [onMessage, loadCurrentRound, navigate, roomCode]);
  
  // Auto-advance to next round after showing results (host only)
  useEffect(() => {
    if (!showResults || !user || !game || game.host !== user.id) return;
    
    const timer = setTimeout(() => {
      advanceToNextRound();
    }, 12000); // Wait 12 seconds after results (time to view results + loading screen)
    
    return () => clearTimeout(timer);
  }, [showResults, user, game, advanceToNextRound]);
  
  // Initial load
  useEffect(() => {
    loadGame();
    loadCurrentRound();
  }, [loadGame, loadCurrentRound]);
  
  // Handle answer submission
  const handleAnswerSubmit = async (answer: string) => {
    if (!roomCode || !currentRound || hasAnswered) return;
    
    setSelectedAnswer(answer);
    setHasAnswered(true);
    
    const responseTime = currentRound.duration - timeRemaining;
    
    try {
      // Submit answer to backend — response contains points_earned
      const answerResult = await gameService.submitAnswer(roomCode, {
        answer,
        response_time: responseTime
      });
      
      // Store the player's own points for immediate display
      setMyPointsEarned(answerResult.points_earned || 0);
      
      // Notify other players via WebSocket
      sendMessage({
        type: 'player_answer',
        player: user?.username || 'You',
        answer: answer,
        response_time: responseTime
      });
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };

  // ─── Render the correct question component based on game mode ───
  const renderQuestionComponent = () => {
    if (!currentRound) return null;

    const commonProps = {
      round: currentRound,
      onAnswerSubmit: handleAnswerSubmit,
      hasAnswered,
      selectedAnswer,
      showResults,
      roundResults,
    };

    const mode = game?.mode;
    switch (mode) {
      case 'blind_test_inverse':
        return <BlindTestInverse {...commonProps} />;
      case 'guess_year':
        return <YearQuestion {...commonProps} />;
      case 'guess_artist':
        return <GuessArtistQuestion {...commonProps} />;
      case 'intro':
        return <IntroQuestion {...commonProps} />;
      case 'lyrics':
        return currentRound.question_type === 'lyrics'
          ? <LyricsQuestion {...commonProps} />
          : <QuizQuestion {...commonProps} />;
      default:
        return <QuizQuestion {...commonProps} />;
    }
  };

  // ─── Mode display name for header ───
  const getModeLabel = () => {
    switch (game?.mode) {
      case 'blind_test_inverse': return '🎯 Trouver le Titre';
      case 'guess_year': return '📅 Année de Sortie';
      case 'guess_artist': return '🎤 Trouver l\'Artiste';
      case 'intro': return '⚡ Intro (3s)';
      case 'lyrics': return '📝 Lyrics';
      default: return '🎵 Quiz';
    }
  };

  // Callback when loading screen completes
  const handleLoadingComplete = () => {
    setRoundPhase('playing');
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl">Chargement...</div>
      </div>
    );
  }
  
  if (!currentRound) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl">En attente du prochain round...</div>
      </div>
    );
  }

  // Show loading screen before round starts
  if (roundPhase === 'loading') {
    return (
      <RoundLoadingScreen
        roundNumber={currentRound.round_number}
        onComplete={handleLoadingComplete}
        duration={10}
      />
    );
  }

  // Show results screen after round ends
  if (roundPhase === 'results' && roundResults) {
    return (
      <RoundResultsScreen
        round={currentRound}
        players={game?.players || []}
        correctAnswer={roundResults.correct_answer || currentRound.correct_answer || ''}
        myPointsEarned={myPointsEarned}
      />
    );
  }
  
  // Show game screen during round
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      <div className="container mx-auto max-w-6xl">
        {/* Header with room code and round number */}
        <div className="flex justify-between items-center mb-6">
          <div className="text-white">
            <h1 className="text-2xl font-bold">Partie {roomCode}</h1>
            <p className="text-lg">Round {currentRound.round_number} — {getModeLabel()}</p>
          </div>
          
          {/* Timer */}
          <div className={`text-6xl font-bold ${
            timeRemaining <= 5 ? 'text-red-400 animate-pulse' : 'text-white'
          }`}>
            {timeRemaining}s
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main quiz area */}
          <div className="lg:col-span-2">
            {renderQuestionComponent()}
          </div>
          
          {/* Live scoreboard */}
          <div className="lg:col-span-1">
            <LiveScoreboard players={game?.players || []} />
          </div>
        </div>
      </div>
    </div>
  );
}

