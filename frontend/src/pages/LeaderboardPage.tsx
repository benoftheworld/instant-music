import { LoadingState } from '@/components/ui';
import { useLeaderboardPage } from '@/hooks/pages/useLeaderboardPage';
import PlayerLeaderboard from '@/components/leaderboard/PlayerLeaderboard';
import TeamLeaderboard from '@/components/leaderboard/TeamLeaderboard';

export default function LeaderboardPage() {
  const {
    user,
    selectedMode,
    page,
    pageSize,
    goNext,
    goPrev,
    players,
    teams,
    totalCount,
    loading,
    error,
    handleModeChange,
    primaryTabs,
    modeTabs,
    subtitleMap,
  } = useLeaderboardPage();

  return (
    <div className="min-h-screen bg-cream-100 text-dark">
      <div className="container mx-auto max-w-5xl px-4 py-10 space-y-8">
        {/* ── Header ──────────────────────────────────────────── */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">Classement</h1>
          <p className="text-dark-300 text-sm sm:text-base">
            {subtitleMap[selectedMode] ?? ''}
          </p>
        </div>

        {/* ── Tabs ───────────────────────────────────────────── */}
        <div className="space-y-3">
          <div className="flex justify-center gap-2">
            {primaryTabs.map((tab) => (
              <button
                key={tab.value}
                onClick={() => handleModeChange(tab.value)}
                className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                  selectedMode === tab.value
                    ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25'
                    : 'bg-cream-200 text-dark-400 hover:bg-cream-300 hover:text-dark border border-cream-300'
                }`}
              >
                <span className="mr-1.5">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap justify-center gap-1.5">
            {modeTabs.map((tab) => (
              <button
                key={tab.value}
                onClick={() => handleModeChange(tab.value)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  selectedMode === tab.value
                    ? 'bg-primary-500 text-white'
                    : 'bg-cream-200 text-dark-300 hover:bg-cream-300 hover:text-dark-400'
                }`}
              >
                <span className="mr-1">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* ── Content ────────────────────────────────────────── */}
        {loading ? (
          <LoadingState message="Chargement du classement..." />
        ) : error ? (
          <div className="text-center py-16">
            <p className="text-red-600">{error}</p>
          </div>
        ) : selectedMode === 'teams' ? (
          <TeamLeaderboard
            teams={teams}
            page={page}
            totalCount={totalCount}
            pageSize={pageSize}
            onPrev={goPrev}
            onNext={goNext}
          />
        ) : (
          <PlayerLeaderboard
            players={players}
            currentUserId={user?.id}
            page={page}
            totalCount={totalCount}
            pageSize={pageSize}
            onPrev={goPrev}
            onNext={goNext}
          />
        )}
      </div>
    </div>
  );
}
