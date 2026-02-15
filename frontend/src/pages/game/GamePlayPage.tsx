import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { gameService } from '../../services/gameService';
import { useWebSocket } from '../../hooks/useWebSocket';
import QuizQuestion from '../../components/game/QuizQuestion';
import LiveScoreboard from '../../components/game/LiveScoreboard';

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

export default function GamePlayPage() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();
  
  const [game, setGame] = useState<any>(null);
  const [currentRound, setCurrentRound] = useState<Round | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const [hasAnswered, setHasAnswered] = useState(false);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [roundResults, setRoundResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
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
  
  // Timer countdown
  useEffect(() => {
    if (!currentRound || hasAnswered || showResults) return;
    
    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(interval);
  }, [currentRound, hasAnswered, showResults]);
  
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
          break;
          
        case 'player_answered':
          // Another player answered
          console.log('Player answered:', data.player);
          break;
          
        case 'round_ended':
          // Round finished, show results
          setShowResults(true);
          setRoundResults(data.results);
          break;
          
        case 'next_round':
          // Move to next round automatically
          loadCurrentRound();
          break;
          
        case 'game_finished':
          // Game over
          navigate(`/game/${roomCode}/results`);
          break;
      }
    });
    
    return unsubscribe;
  }, [onMessage, loadCurrentRound, navigate, roomCode]);
  
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
      // Submit answer to backend
      await gameService.submitAnswer(roomCode, {
        answer,
        response_time: responseTime
      });
      
      // Notify other players via WebSocket
      sendMessage({
        type: 'player_answer',
        player: (game?.players?.find((p: any) => p.id === 'current') as any)?.username || 'You',
        answer: answer,
        response_time: responseTime
      });
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
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
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      <div className="container mx-auto max-w-6xl">
        {/* Header with room code and round number */}
        <div className="flex justify-between items-center mb-6">
          <div className="text-white">
            <h1 className="text-2xl font-bold">Partie {roomCode}</h1>
            <p className="text-lg">Round {currentRound.round_number}</p>
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
            <QuizQuestion
              round={currentRound}
              onAnswerSubmit={handleAnswerSubmit}
              hasAnswered={hasAnswered}
              selectedAnswer={selectedAnswer}
              showResults={showResults}
              roundResults={roundResults}
            />
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

