import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { teamService } from '@/services/socialService';
import { getMediaUrl } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import type { Team, TeamMember, TeamMemberRole } from '@/types';

export default function TeamPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const [team, setTeam] = useState<Team | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [editing, setEditing] = useState(false);
  const [editDescription, setEditDescription] = useState('');
  const [editAvatarFile, setEditAvatarFile] = useState<File | null>(null);
  const [joinRequests, setJoinRequests] = useState<any[]>([]);
  const [requestsLoading, setRequestsLoading] = useState(false);

  const roleLabel = (role?: string) => {
    if (!role) return '';
    const map: Record<string, string> = {
      owner: 'Propriétaire',
      admin: 'Administrateur',
      member: 'Membre',
    };
    return map[role] || role;
  };

  useEffect(() => {
    if (!id) return navigate('/teams');
    fetchTeam();
  }, [id]);

  useEffect(() => {
    if (!team) return;
    if (!canManage()) return;
    fetchRequests();
  }, [team]);

  const fetchTeam = async () => {
    setLoading(true);
    try {
      const data = await teamService.getTeam(Number(id));
      setTeam(data);
      setEditDescription(data.description || '');
    } catch (err) {
      setMessage({ type: 'error', text: 'Impossible de charger l\'équipe.' });
    } finally {
      setLoading(false);
    }
  };

  const fetchRequests = async () => {
    if (!team) return;
    setRequestsLoading(true);
    try {
      const data = await teamService.getJoinRequests(team.id);
      setJoinRequests(Array.isArray(data) ? data : (data as any)?.results || []);
    } catch (err: any) {
      // ignore for now
    } finally {
      setRequestsLoading(false);
    }
  };

  const canManage = () => {
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

  const handleApproveRequest = async (requestId: number) => {
    if (!team) return;
    setProcessing(true);
    try {
      await teamService.approveJoinRequest(team.id, requestId);
      setMessage({ type: 'success', text: 'Demande approuvée.' });
      fetchTeam();
      fetchRequests();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.error || 'Erreur.' });
    } finally {
      setProcessing(false);
    }
  };

  const handleRejectRequest = async (requestId: number) => {
    if (!team) return;
    if (!confirm('Refuser cette demande ?')) return;
    setProcessing(true);
    try {
      await teamService.rejectJoinRequest(team.id, requestId);
      setMessage({ type: 'success', text: 'Demande refusée.' });
      fetchRequests();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.error || 'Erreur.' });
    } finally {
      setProcessing(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!team) return;
    const fd = new FormData();
    fd.append('description', editDescription || '');
    if (editAvatarFile) fd.append('avatar', editAvatarFile);

    setProcessing(true);
    try {
      const updated = await teamService.updateTeam(team.id, fd);
      setTeam(updated);
      setMessage({ type: 'success', text: 'Équipe mise à jour.' });
      setEditing(false);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.error || 'Erreur lors de la mise à jour.' });
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
            {editing ? (
              <form onSubmit={handleEditSubmit} className="space-y-2">
                <textarea
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  className="input w-full"
                  placeholder="Description de l'équipe"
                  maxLength={500}
                />
                <div className="flex items-center gap-2">
                  <input type="file" accept="image/*" onChange={(e) => setEditAvatarFile(e.target.files?.[0] || null)} />
                  <button type="submit" disabled={processing} className="btn-primary">{processing ? 'Enregistrement...' : 'Enregistrer'}</button>
                  <button type="button" onClick={() => setEditing(false)} className="text-sm text-gray-500">Annuler</button>
                </div>
              </form>
            ) : (
              <p className="text-sm text-gray-600">{team.description}</p>
            )}
            <div className="flex gap-4 mt-2 text-sm text-gray-500">
              <span>👥 {team.member_count} membres</span>
              <span>🎮 {team.total_games} parties</span>
              <span>🏆 {team.total_wins} victoires</span>
              <span>⭐ {team.total_points} pts</span>
            </div>
          </div>
          {canManage() && !editing && (
            <div className="ml-auto">
              <button onClick={() => setEditing(true)} className="btn-primary">Modifier l'équipe</button>
            </div>
          )}
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
                  {m.user.avatar ? (
                    <img src={getMediaUrl(m.user.avatar)} alt={m.user.username} className="w-10 h-10 rounded-full object-cover" />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-blue-500 flex items-center justify-center text-white font-bold">
                      {m.user.username.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div>
                    <div className="font-medium">{m.user.username}</div>
                    <div className="text-xs text-gray-500">Points: {m.user.total_points ?? '—'} · Victoires: {m.user.total_wins ?? '—'}</div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {canManage() ? (
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
                    <span className="text-sm text-gray-600">{roleLabel(m.role)}</span>
                  )}

                  {canManage() && m.role !== 'owner' && (
                    <button onClick={() => handleRemove(m)} className="text-sm text-red-500">Supprimer</button>
                  )}
                </div>
              </div>
            ))}
          </div>
          </div>

          {canManage() && (
            <div className="card mt-4">
              <h2 className="text-lg font-bold mb-4">Demandes d'adhésion</h2>
              {requestsLoading ? (
                <div>Chargement...</div>
              ) : joinRequests.length === 0 ? (
                <div className="text-sm text-gray-500">Aucune demande en attente.</div>
              ) : (
                <div className="space-y-2">
                  {joinRequests.map((r) => (
                    <div key={r.id} className="flex items-center justify-between p-2 border border-gray-100 rounded">
                      <div className="flex items-center gap-3">
                        {r.user.avatar ? (
                          <img src={getMediaUrl(r.user.avatar)} alt={r.user.username} className="w-10 h-10 rounded-full object-cover" />
                        ) : (
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-blue-500 flex items-center justify-center text-white font-bold">
                            {r.user.username.charAt(0).toUpperCase()}
                          </div>
                        )}
                        <div>
                          <div className="font-medium">{r.user.username}</div>
                          <div className="text-xs text-gray-500">{r.message || ''}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button onClick={() => handleApproveRequest(r.id)} disabled={processing} className="btn-primary text-sm">Accepter</button>
                        <button onClick={() => handleRejectRequest(r.id)} disabled={processing} className="text-sm text-red-500">Refuser</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
      </div>
    </div>
  );
}
