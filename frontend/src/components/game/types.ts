import type { GameRound } from '@/types';

export interface RoundResults {
  correct_answer: string;
  points_earned?: number;
}

export interface Props {
  round: GameRound;
  onAnswerSubmit: (answer: string) => void;
  hasAnswered: boolean;
  selectedAnswer: string | null;
  showResults: boolean;
  roundResults: RoundResults | null;
  seekOffsetMs?: number;
  excludedOptions?: string[];
  fogBlur?: boolean;
}

export type { GameRound };
