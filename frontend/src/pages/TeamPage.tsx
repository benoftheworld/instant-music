import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { teamService } from '@/services/socialService';
import { getApiErrorMessage } from '@/utils/apiError';
import { getMediaUrl } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { Alert, Avatar, PageLoader } from '@/components/ui';
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

  const fetchTeam = useCallback(async () => {
    setLoading(true);
    try {
      const data = await teamService.getTeam(id as string);
      setTeam(data);
      setEditDescription(data.description || '');
    } catch (err) {
      setMessage({ type: 'error', text: 'Impossible de charger l\'équipe.' });
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (!id) return navigate('/teams');
    fetchTeam();
  }, [id, navigate, fetchTeam]);

  const fetchRequests = useCallback(async () => {
    if (!team) return;
    setRequestsLoading(true);
    try {
      const data = await teamService.getJoinRequests(team.id);
      setJoinRequests(Array.isArray(data) ? data : (data as any)?.results || []);
    } catch (err: unknown) {
      // ignore for now
    } finally {
      setRequestsLoading(false);
    }
  }, [team]);

  const canManage = useCallback(() => {
    if (!team || !user) return false;
    const myMembership = team.members_list.find(m => m.user.id === user.id);
    if (!myMembership) return false;
    return myMembership.role === 'owner' || myMembership.role === 'admin';
  }, [team, user]);

  useEffect(() => {
    if (!team) return;
    if (!canManage()) return;
    fetchRequests();
  }, [team, canManage, fetchRequests]);


  const handleChangeRole = async (member: TeamMember, role: TeamMemberRole) => {
    if (!team) return;
    setProcessing(true);
    try {
      await teamService.updateMemberRole(team.id, member.id, role);
      setMessage({ type: 'success', text: 'Rôle mis à jour.' });
      fetchTeam();
    } catch (err: unknown) {
      setMessage({ type: 'error', text: getApiErrorMessage(err, 'Erreur.') });
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
    } catch (err: unknown) {
      setMessage({ type: 'error', text: getApiErrorMessage(err, 'Erreur.') });
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
    } catch (err: unknown) {
      setMessage({ type: 'error', text: getApiErrorMessage(err, 'Erreur.') });
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
    } catch (err: unknown) {
      setMessage({ type: 'error', text: getApiErrorMessage(err, 'Erreur.') });
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
    } catch (err: unknown) {
      setMessage({ type: 'error', text: getApiErrorMessage(err, 'Erreur lors de la mise à jour.') });
    } finally {
      setProcessing(false);
    }
  };

  const handleDissolve = async () => {
    if (!team) return;
    if (!confirm(`Dissoudre l'équipe "${team.name}" ? Tous les membres seront exclus et l'équipe sera supprimée définitivement.`)) return;
    setProcessing(true);
    try {
      await teamService.dissolveTeam(team.id);
      navigate('/teams');
    } catch (err: unknown) {
      setMessage({ type: 'error', text: getApiErrorMessage(err, 'Erreur lors de la dissolution.') });
      setProcessing(false);
    }
  };

  if (loading) return <PageLoader message="Chargement de l'équipe..." />;
  if (!team) return <div className="container mx-auto px-4 py-8">Équipe introuvable.</div>;

  const myMembership = team.members_list.find(m => m.user.id === user?.id);
  const isOwner = myMembership?.role === 'owner';

  return (
    <div className="container mx-auto px-4 py-6 sm:py-8">
      <div className="max-w-4xl mx-auto">
        {/* Team header */}
        <div className="flex flex-col sm:flex-row sm:items-start gap-4 mb-6">
          <div className="flex items-start gap-4">
            {team.avatar ? (
              <img src={getMediaUrl(team.avatar)} alt={team.name} className="w-16 h-16 sm:w-20 sm:h-20 rounded-lg object-cover flex-shrink-0" />
            ) : (
              <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-lg bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-2xl sm:text-3xl font-bold flex-shrink-0">
                {team.name.charAt(0).toUpperCase()}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <h1 className="text-xl sm:text-2xl font-bold">{team.name}</h1>
              {!editing && (
                <p className="text-sm text-gray-600 mt-1">{team.description}</p>
              )}
              <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2 text-xs sm:text-sm text-gray-500">
                <span>👥 {team.member_count} membres</span>
                <span>🎮 {team.total_games} parties</span>
                <span>🏆 {team.total_wins} victoires</span>
                <span>⭐ {team.total_points} pts</span>
              </div>
            </div>
          </div>
          {!editing && (
            <div className="flex flex-col gap-2 sm:ml-auto self-start sm:self-auto">
              {canManage() && (
                <button onClick={() => setEditing(true)} className="btn-primary text-sm">
                  Modifier l'équipe
                </button>
              )}
              {isOwner && (
                <button
                  onClick={handleDissolve}
                  disabled={processing}
                  className="text-sm text-red-600 border border-red-300 rounded px-3 py-1.5 hover:bg-red-50 transition-colors"
                >
                  Dissoudre l'équipe
                </button>
              )}
            </div>
          )}
        </div>

        {/* Edit form */}
        {editing && (
          <div className="card mb-6">
            <h2 className="text-lg font-bold mb-3">Modifier l'équipe</h2>
            <form onSubmit={handleEditSubmit} className="space-y-3">
              <textarea
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                className="input w-full"
                placeholder="Description de l'équipe"
                maxLength={500}
              />
              <div className="flex flex-col sm:flex-row gap-2">
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setEditAvatarFile(e.target.files?.[0] || null)}
                  className="text-sm"
                />
                <div className="flex gap-2">
                  <button type="submit" disabled={processing} className="btn-primary">
                    {processing ? 'Enregistrement...' : 'Enregistrer'}
                  </button>
                  <button type="button" onClick={() => setEditing(false)} className="text-sm text-gray-500">
                    Annuler
                  </button>
                </div>
              </div>
            </form>
          </div>
        )}

        {message && (
          <Alert
            variant={message.type}
            onClose={() => setMessage(null)}
            className="mb-4"
          >
            {message.text}
          </Alert>
        )}

        <div className="card">
          <h2 className="text-lg font-bold mb-4">Membres</h2>
          <div className="space-y-2">
            {team.members_list.map((m) => (
              <div key={m.id} className="flex flex-col sm:flex-row sm:items-center gap-2 p-2 border border-gray-100 rounded">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  {m.user.avatar ? (
                    <img src={getMediaUrl(m.user.avatar)} alt={m.user.username} className="w-9 h-9 sm:w-10 sm:h-10 rounded-full object-cover flex-shrink-0" />
                  ) : (
                    <Avatar username={m.user.username} size="sm" className="flex-shrink-0" />
                  )}
                  <div className="min-w-0">
                    <div className="font-medium truncate">{m.user.username}</div>
                    <div className="text-xs text-gray-500">Pts: {m.user.total_points ?? '—'} · Victoires: {m.user.total_wins ?? '—'}</div>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {canManage() ? (
                    <select
                      value={m.role}
                      onChange={(e) => handleChangeRole(m, e.target.value as TeamMemberRole)}
                      disabled={processing || (m.role === 'owner' && !isOwner)}
                      className="input text-sm py-1"
                    >
                      <option value="member">Membre</option>
                      <option value="admin">Admin</option>
                      <option value="owner">Proprio</option>
                    </select>
                  ) : (
                    <span className="text-sm text-gray-600">{roleLabel(m.role)}</span>
                  )}

                  {canManage() && m.role !== 'owner' && (
                    <button onClick={() => handleRemove(m)} className="text-sm text-red-500 whitespace-nowrap">
                      Retirer
                    </button>
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
                    <div key={r.id} className="flex flex-col sm:flex-row sm:items-center gap-2 p-2 border border-gray-100 rounded">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        {r.user.avatar ? (
                          <img src={getMediaUrl(r.user.avatar)} alt={r.user.username} className="w-9 h-9 rounded-full object-cover flex-shrink-0" />
                        ) : (
                          <Avatar username={r.user.username} size="sm" className="flex-shrink-0" />
                        )}
                        <div className="min-w-0">
                          <div className="font-medium truncate">{r.user.username}</div>
                          <div className="text-xs text-gray-500">{r.message || ''}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button onClick={() => handleApproveRequest(r.id)} disabled={processing} className="btn-primary text-sm py-1">Accepter</button>
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
