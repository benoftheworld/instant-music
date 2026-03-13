import { useNavigate } from 'react-router-dom';
import { getMediaUrl } from '@/services/api';
import { Alert, Button, EmptyState, LoadingState } from '@/components/ui';
import type { Team } from '@/types';
import { useTeamsPage } from '@/hooks/pages/useTeamsPage';

export default function TeamsPage() {
  const {
    user,
    activeTab,
    setActiveTab,
    message,
    setMessage,
    newTeamName,
    setNewTeamName,
    newTeamDescription,
    setNewTeamDescription,
    creating,
    allTeams,
    loading,
    handleCreateTeam,
    handleJoinTeam,
    isInTeam,
  } = useTeamsPage();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">Équipes</h1>
          <p className="text-gray-600">Créez ou rejoignez des équipes pour jouer ensemble</p>
        </div>

        {/* Message */}
        {message && (
          <Alert
            variant={message.type}
            onClose={() => setMessage(null)}
            className="mb-4"
          >
            {message.text}
          </Alert>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('browse')}
            className={`px-4 py-2 rounded-lg font-medium ${
              activeTab === 'browse' ? 'bg-primary-500 text-white' : 'bg-cream-200 text-dark-400 hover:bg-cream-300'
            }`}
          >
            Parcourir ({allTeams.length})
          </button>
          <button
            onClick={() => setActiveTab('create')}
            className={`px-4 py-2 rounded-lg font-medium ${
              activeTab === 'create' ? 'bg-primary-500 text-white' : 'bg-cream-200 text-dark-400 hover:bg-cream-300'
            }`}
          >
            + Créer
          </button>
        </div>

        {/* My Teams Tab */}
        {/* Removed 'Mes équipes' tab — users are redirected to team detail pages */}

        {/* Browse Tab */}
        {activeTab === 'browse' && (
          <div className="space-y-4">
            {loading ? (
              <LoadingState message="Chargement..." />
            ) : allTeams.length === 0 ? (
              <EmptyState
                title="Aucune équipe disponible"
                action={
                  <Button onClick={() => setActiveTab('create')}>Créer la première équipe</Button>
                }
              />
            ) : (
              allTeams.map((team) => (
                <TeamCard
                  key={team.id}
                  team={team}
                  currentUserId={user?.id}
                  onJoin={() => handleJoinTeam(team.id)}
                  isJoined={isInTeam(team.id)}
                />
              ))
            )}
          </div>
        )}

        {/* Create Tab */}
        {activeTab === 'create' && (
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Créer une équipe</h2>
            <form onSubmit={handleCreateTeam} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nom de l'équipe *
                </label>
                <input
                  type="text"
                  value={newTeamName}
                  onChange={(e) => setNewTeamName(e.target.value)}
                  className="input"
                  placeholder="Les Champions"
                  required
                  maxLength={100}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={newTeamDescription}
                  onChange={(e) => setNewTeamDescription(e.target.value)}
                  className="input min-h-[100px]"
                  placeholder="Une super équipe qui aime la musique..."
                  maxLength={500}
                />
              </div>
              <Button
                type="submit"
                loading={creating}
                disabled={!newTeamName.trim()}
                className="w-full"
              >
                Créer l'\u00e9quipe
              </Button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}

interface TeamCardProps {
  team: Team;
  currentUserId?: number;
  onJoin?: () => void;
  onLeave?: () => void;
  isJoined?: boolean;
  showLeave?: boolean;
}

function TeamCard({ team, currentUserId, onJoin, onLeave, isJoined, showLeave }: TeamCardProps) {
  const isOwner = team.owner.id === currentUserId;
  const navigate = useNavigate();

  const handleView = (e: React.MouseEvent) => {
    // prevent buttons inside the card from triggering navigation
    const target = e.target as HTMLElement;
    if (target.tagName === 'BUTTON' || target.tagName === 'SELECT' || target.closest('button')) return;
    navigate(`/teams/${team.id}`);
  };

  return (
    <div onClick={handleView} className="card border border-gray-200 cursor-pointer">
      <div className="flex items-start gap-3 sm:gap-4">
        {team.avatar ? (
          <img
            src={getMediaUrl(team.avatar)}
            alt={team.name}
            className="w-14 h-14 sm:w-16 sm:h-16 rounded-lg object-cover flex-shrink-0"
          />
        ) : (
          <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-lg bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-2xl font-bold flex-shrink-0">
            {team.name.charAt(0).toUpperCase()}
          </div>
        )}
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-base sm:text-lg font-bold">{team.name}</h3>
            {isOwner && (
              <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full">
                Propriétaire
              </span>
            )}
          </div>
          {team.description && (
            <p className="text-sm text-gray-600 mt-1 line-clamp-2">{team.description}</p>
          )}
          
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2 text-xs sm:text-sm text-gray-500">
            <span>👥 {team.member_count} membres</span>
            <span>🎮 {team.total_games} parties</span>
            <span>🏆 {team.total_wins} victoires</span>
            <span>⭐ {team.total_points} pts</span>
          </div>
        </div>

        <div className="flex flex-col gap-2 flex-shrink-0">
          {onJoin && !isJoined && (
            <button onClick={onJoin} className="btn-primary text-sm">
              Rejoindre
            </button>
          )}
          {isJoined && !showLeave && (
            <span className="text-sm text-green-600 font-medium">✓ Membre</span>
          )}
          {showLeave && onLeave && !isOwner && (
            <button
              onClick={onLeave}
              className="text-sm text-red-500 hover:text-red-700"
            >
              Quitter
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
