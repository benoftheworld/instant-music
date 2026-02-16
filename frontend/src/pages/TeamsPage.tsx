import { useState, useEffect } from 'react';
import { teamService } from '@/services/socialService';
import { getMediaUrl } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import type { Team } from '@/types';

export default function TeamsPage() {
  const user = useAuthStore((state) => state.user);
  const [myTeams, setMyTeams] = useState<Team[]>([]);
  const [allTeams, setAllTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'my' | 'browse' | 'create'>('my');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  // Create form
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamDescription, setNewTeamDescription] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [myData, allData] = await Promise.all([
        teamService.getMyTeams(),
        teamService.browseTeams(),
      ]);
      // Handle paginated or direct array response
      setMyTeams(Array.isArray(myData) ? myData : (myData as any)?.results || []);
      setAllTeams(Array.isArray(allData) ? allData : (allData as any)?.results || []);
    } catch (err) {
      console.error('Failed to fetch teams:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTeamName.trim()) return;
    
    setCreating(true);
    try {
      const team = await teamService.createTeam({
        name: newTeamName,
        description: newTeamDescription,
      });
      setMyTeams([...myTeams, team]);
      setNewTeamName('');
      setNewTeamDescription('');
      setMessage({ type: 'success', text: `Équipe "${team.name}" créée !` });
      setActiveTab('my');
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.name?.[0] || 'Erreur lors de la création' });
    } finally {
      setCreating(false);
    }
  };

  const handleJoinTeam = async (teamId: number) => {
    try {
      const team = await teamService.joinTeam(teamId);
      setMyTeams([...myTeams, team]);
      setMessage({ type: 'success', text: `Vous avez rejoint "${team.name}" !` });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.error || 'Erreur' });
    }
  };

  const handleLeaveTeam = async (teamId: number) => {
    if (!window.confirm('Quitter cette équipe ?')) return;
    try {
      await teamService.leaveTeam(teamId);
      setMyTeams(myTeams.filter(t => t.id !== teamId));
      setMessage({ type: 'success', text: 'Vous avez quitté l\'équipe' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.error || 'Erreur' });
    }
  };

  const isInTeam = (teamId: number) => myTeams.some(t => t.id === teamId);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">🎯 Équipes</h1>
          <p className="text-gray-600">Créez ou rejoignez des équipes pour jouer ensemble</p>
        </div>

        {/* Message */}
        {message && (
          <div className={`mb-4 p-3 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}>
            {message.text}
            <button onClick={() => setMessage(null)} className="float-right">&times;</button>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('my')}
            className={`px-4 py-2 rounded-lg font-medium ${
              activeTab === 'my' ? 'bg-primary-500 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            Mes équipes ({myTeams.length})
          </button>
          <button
            onClick={() => setActiveTab('browse')}
            className={`px-4 py-2 rounded-lg font-medium ${
              activeTab === 'browse' ? 'bg-primary-500 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            Parcourir
          </button>
          <button
            onClick={() => setActiveTab('create')}
            className={`px-4 py-2 rounded-lg font-medium ${
              activeTab === 'create' ? 'bg-primary-500 text-white' : 'bg-gray-100 text-gray-700'
            }`}
          >
            + Créer
          </button>
        </div>

        {/* My Teams Tab */}
        {activeTab === 'my' && (
          <div className="space-y-4">
            {loading ? (
              <div className="text-center py-8 text-gray-400">Chargement...</div>
            ) : myTeams.length === 0 ? (
              <div className="card text-center py-8">
                <p className="text-gray-400 mb-4">Vous n'êtes dans aucune équipe</p>
                <button
                  onClick={() => setActiveTab('browse')}
                  className="btn-primary"
                >
                  Parcourir les équipes
                </button>
              </div>
            ) : (
              myTeams.map((team) => (
                <TeamCard
                  key={team.id}
                  team={team}
                  currentUserId={user?.id}
                  onLeave={() => handleLeaveTeam(team.id)}
                  showLeave
                />
              ))
            )}
          </div>
        )}

        {/* Browse Tab */}
        {activeTab === 'browse' && (
          <div className="space-y-4">
            {loading ? (
              <div className="text-center py-8 text-gray-400">Chargement...</div>
            ) : allTeams.length === 0 ? (
              <div className="card text-center py-8">
                <p className="text-gray-400 mb-4">Aucune équipe disponible</p>
                <button
                  onClick={() => setActiveTab('create')}
                  className="btn-primary"
                >
                  Créer la première équipe
                </button>
              </div>
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
              <button
                type="submit"
                disabled={creating || !newTeamName.trim()}
                className="btn-primary w-full"
              >
                {creating ? 'Création...' : 'Créer l\'équipe'}
              </button>
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

  return (
    <div className="card border border-gray-200">
      <div className="flex items-start gap-4">
        {team.avatar ? (
          <img
            src={getMediaUrl(team.avatar)}
            alt={team.name}
            className="w-16 h-16 rounded-lg object-cover"
          />
        ) : (
          <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-purple-400 to-blue-500 flex items-center justify-center text-white text-2xl font-bold">
            {team.name.charAt(0).toUpperCase()}
          </div>
        )}
        
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold">{team.name}</h3>
            {isOwner && (
              <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full">
                Propriétaire
              </span>
            )}
          </div>
          {team.description && (
            <p className="text-sm text-gray-600 mt-1">{team.description}</p>
          )}
          
          <div className="flex gap-4 mt-3 text-sm text-gray-500">
            <span>👥 {team.member_count} membres</span>
            <span>🎮 {team.total_games} parties</span>
            <span>🏆 {team.total_wins} victoires</span>
            <span>⭐ {team.total_points} pts</span>
          </div>
        </div>

        <div className="flex flex-col gap-2">
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
