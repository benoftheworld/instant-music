import { StatCard, MiniStat } from '@/components/ui/StatCard';
import type { User } from '@/types';
import type { UserDetailedStats } from '@/types';

interface Props {
  user: User;
  detailedStats: UserDetailedStats | null;
}

function SectionTitle({ icon, title }: { icon: string; title: string }) {
  return (
    <h2 className="text-xl font-bold text-dark flex items-center gap-2">
      <span>{icon}</span>
      {title}
    </h2>
  );
}

function ProgressStat({
  label,
  value,
  max,
  format,
  color,
}: {
  label: string;
  value: number;
  max: number;
  format: (v: number) => string;
  color: string;
}) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm font-bold text-dark">{format(value)}</span>
      </div>
      <div className="h-2 rounded-full bg-cream-300 overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function ProfileStats({ user, detailedStats }: Props) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon="" label="Parties jouées" value={user.total_games_played} textColor="text-primary-600" bgClass="bg-primary-50 border-primary-200" />
        <StatCard icon="" label="Victoires" value={user.total_wins} textColor="text-primary-600" bgClass="bg-primary-50 border-primary-200" />
        <StatCard icon="" label="Taux de victoire" value={`${(user.win_rate ?? 0).toFixed(1)}%`} textColor="text-primary-600" bgClass="bg-primary-50 border-primary-200" />
        <StatCard icon="" label="Points totaux" value={user.total_points} textColor="text-primary-600" bgClass="bg-primary-50 border-primary-200" />
      </div>

      {detailedStats ? (
        <div className="card space-y-6">
          <SectionTitle icon="" title="Performance" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MiniStat label="Score moyen" value={detailedStats.avg_score_per_game.toFixed(0)} />
            <MiniStat label="Meilleur score" value={String(detailedStats.best_score)} highlight />
            <MiniStat label="Temps moyen" value={`${detailedStats.avg_response_time.toFixed(1)}s`} />
            <MiniStat label="Réponses totales" value={String(detailedStats.total_answers)} />
          </div>
          <div className="space-y-4 pt-2 border-t border-cream-200">
            <ProgressStat
              label="Précision des réponses"
              value={detailedStats.accuracy}
              max={100}
              format={(v) => `${v.toFixed(1)}%`}
              color="bg-primary-500"
            />
            <ProgressStat
              label="Taux de victoire"
              value={user.win_rate ?? 0}
              max={100}
              format={(v) => `${v.toFixed(1)}%`}
              color="bg-green-500"
            />
            <ProgressStat
              label="Réponses correctes"
              value={detailedStats.total_correct_answers}
              max={detailedStats.total_answers || 1}
              format={(v) => `${v} / ${detailedStats.total_answers}`}
              color="bg-primary-500"
            />
          </div>
        </div>
      ) : (
        <div className="card text-center py-12 text-gray-400">
          <div className="text-4xl mb-3">📊</div>
          <p>Chargement des statistiques…</p>
        </div>
      )}
    </div>
  );
}
