import type { GameRound } from './types';

export function TrackReveal({ round }: { round: GameRound }) {
  return (
    <div className="mb-3 md:mb-4 rounded-lg overflow-hidden shadow-lg bg-primary-600 px-4 py-3 md:px-6 md:py-4">
      <div className="text-white text-center">
        <p className="text-base md:text-lg font-bold">🎶 {round.track_name}</p>
        <p className="text-xs md:text-sm opacity-80">{round.artist_name}</p>
      </div>
    </div>
  );
}
