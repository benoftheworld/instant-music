import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { gameService } from '../../services/gameService';
import type { GamePlayer } from '@/types';

interface RoundAnswer {
  username: string;
  answer: string;
  is_correct: boolean;
  points_earned: number;
  response_time: number;
  consecutive_correct?: number;
  streak_bonus?: number;
}

interface RoundBonus {
  username: string;
  bonus_type: string;
}

export interface RoundDetail {
  round_number: number;
  track_name: string;
  artist_name: string;
  correct_answer: string;
  track_id: string;
  answers: RoundAnswer[];
  bonuses: RoundBonus[];
}

export interface GameResult {
  game: {
    id: string;
    room_code: string;
    host: number;
    status: string;
    mode: string;
    mode_display: string;
    answer_mode: string;
    answer_mode_display: string;
    guess_target: string;
    guess_target_display: string;
    num_rounds: number;
    is_party_mode: boolean;
  };
  rankings: GamePlayer[];
  rounds: RoundDetail[];
}

export function useGameResultsPage() {
  const { roomCode } = useParams<{ roomCode: string }>();
  const navigate = useNavigate();

  const [results, setResults] = useState<GameResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [showFullRanking, setShowFullRanking] = useState(false);

  useEffect(() => {
    const loadResults = async () => {
      if (!roomCode) return;
      try {
        const data = await gameService.getResults(roomCode);
        setResults(data as unknown as GameResult);
      } catch (error) {
        console.error('Failed to load results:', error);
      } finally {
        setLoading(false);
      }
    };
    loadResults();
  }, [roomCode]);

  const handleDownloadPdf = async () => {
    if (!roomCode) return;
    setDownloadingPdf(true);
    try {
      await gameService.downloadResultsPdf(roomCode);
    } catch (e) {
      console.error('PDF download failed:', e);
    } finally {
      setDownloadingPdf(false);
    }
  };

  const game = results?.game;

  // En mode soirée, exclure le présentateur (hôte) du classement
  const rankings = game?.is_party_mode
    ? (results?.rankings ?? []).filter(p => String(p.user_id) !== String(game.host))
    : (results?.rankings ?? []);

  const rounds = results?.rounds ?? [];
  const top3 = rankings.slice(0, 3);
  const others = rankings.slice(3);
  const winner = rankings[0] ?? null;

  const podiumOrder = [
    top3[1] ?? null,
    top3[0] ?? null,
    top3[2] ?? null,
  ];

  return {
    roomCode,
    navigate,
    results,
    loading,
    downloadingPdf,
    showFullRanking,
    setShowFullRanking,
    handleDownloadPdf,
    game,
    rankings,
    rounds,
    top3,
    others,
    winner,
    podiumOrder,
  };
}
