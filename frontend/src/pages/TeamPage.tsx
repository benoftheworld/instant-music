import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { teamService } from '@/services/socialService';
import { getMediaUrl } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import type { Team, TeamMember, TeamMemberRole, UserMinimal } from '@/types';

export default function TeamPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const [team, setTeam] = useState<Team | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (!id) return navigate('/teams');
    fetchTeam();
  }, [id]);

  const fetchTeam = async () => {
    setLoading(true);
    try {
      const data = await teamService.getTeam(Number(id));
      setTeam(data);
    } catch (err) {
      setMessage({ type: 'error', text: 'Impossible de charger l\'équipe.' });
    } finally {
      setLoading(false);
    }
  };

  const canManage = (member?: TeamMember) => {
    if (!team || !user) return false;
    const myMembership = team.members_list.find(m => m.user.id === user.id);
    if (!myMembership) return false;
    return myMembership.role === 'owner' || myMembership.role === 'admin';
  };

  const handleChangeRole = async (member: TeamMember, role: TeamMemberRole) => {
    if (!team) return;
    setProcessing(true);
    try {
      await teamService.updateMemberRole(team.id, member.id, role);
      setMessage({ type: 'success', text: 'Rôle mis à jour.' });
      fetchTeam();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.error || 'Erreur.' });
    } finally {
      setProcessing(false);
    }
  };

  const handleRemove = async (member: TeamMember) => {
    if (!team) return;
    if (!confirm(`Supprimer ${member.user.username} ?`)) return;
    setProcessing(true);
    try {
      await teamService.removeMember(team.id, member.id);
      setMessage({ type: 'success', text: 'Membre supprimé.' });
      fetchTeam();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.error || 'Erreur.' });
    } finally {
      setProcessing(false);
    }
  };

  if (loading) return <div className="container mx-auto px-4 py-8">Chargement...</div>;
  if (!team) return <div className="container mx-auto px-4 py-8">Équipe introuvable.</div>;

  const myMembership = team.members_list.find(m => m.user.id === user?.id);
  const isOwner = myMembership?.role === 'owner';

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          {team.avatar ? (
            <img src={getMediaUrl(team.avatar)} alt={team.name} className="w-20 h-20 rounded-lg object-cover" />
          ) : (
            <div className="w-20 h-20 rounded-lg bg-gradient-to-br from-purple-400 to-blue-500 flex items-center justify-center text-white text-3xl font-bold">
              {team.name.charAt(0).toUpperCase()}
            </div>
          )}
          <div>
            <h1 className="text-2xl font-bold">{team.name}</h1>
            <p className="text-sm text-gray-600">{team.description}</p>
            <div className="flex gap-4 mt-2 text-sm text-gray-500">
              <span>👥 {team.member_count} membres</span>
              <span>🎮 {team.total_games} parties</span>
              <span>🏆 {team.total_wins} victoires</span>
              <span>⭐ {team.total_points} pts</span>
            </div>
          </div>
        </div>

        {message && (
          <div className={`mb-4 p-3 rounded-lg ${message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
            {message.text}
            <button onClick={() => setMessage(null)} className="float-right">&times;</button>
          </div>
        )}

        <div className="card">
          <h2 className="text-lg font-bold mb-4">Membres</h2>
          <div className="space-y-2">
            {team.members_list.map((m) => (
              <div key={m.id} className="flex items-center justify-between p-2 border border-gray-100 rounded">
                <div className="flex items-center gap-3">
                  <img src={getMediaUrl(m.user.avatar || '')} alt={m.user.username} className="w-10 h-10 rounded-full object-cover" />
                  <div>
                    <div className="font-medium">{m.user.username}</div>
                    <div className="text-xs text-gray-500">Points: {m.user.total_points ?? '—'}</div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {canManage(m) ? (
                    <select
                      value={m.role}
                      onChange={(e) => handleChangeRole(m, e.target.value as TeamMemberRole)}
                      disabled={processing || (m.role === 'owner' && !isOwner)}
                      className="input text-sm"
                    >
                      <option value="member">Membre</option>
                      <option value="admin">Administrateur</option>
                      <option value="owner">Propriétaire</option>
                    </select>
                  ) : (
                    <span className="text-sm text-gray-600">{m.role}</span>
                  )}

                  {canManage(m) && m.role !== 'owner' && (
                    <button onClick={() => handleRemove(m)} className="text-sm text-red-500">Supprimer</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
