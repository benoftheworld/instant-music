import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { teamService } from '@/services/socialService';
import { getApiErrorMessage } from '@/utils/apiError';
import { useAuthStore } from '@/store/authStore';
import type { Team, TeamMember, TeamMemberRole } from '@/types';

export function useTeamPage() {
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

  const fetchTeam = useCallback(async () => {
    setLoading(true);
    try {
      const data = await teamService.getTeam(id as string);
      setTeam(data);
      setEditDescription(data.description || '');
    } catch (err) {
      setMessage({ type: 'error', text: 'Impossible de charger l\'équipe. ' + getApiErrorMessage(err, '') });
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
      setMessage({ type: 'error', text: 'Impossible de charger les demandes de rejoindre. ' + getApiErrorMessage(err, '') });
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

  const myMembership = team?.members_list.find(m => m.user.id === user?.id);
  const isOwner = myMembership?.role === 'owner';

  const roleLabel = (role?: string) => {
    if (!role) return '';
    const map: Record<string, string> = {
      owner: 'Propriétaire',
      admin: 'Administrateur',
      member: 'Membre',
    };
    return map[role] || role;
  };

  return {
    team,
    loading,
    processing,
    message,
    setMessage,
    editing,
    setEditing,
    editDescription,
    setEditDescription,
    editAvatarFile,
    setEditAvatarFile,
    joinRequests,
    requestsLoading,
    canManage,
    isOwner,
    roleLabel,
    handleChangeRole,
    handleRemove,
    handleApproveRequest,
    handleRejectRequest,
    handleEditSubmit,
    handleDissolve,
  };
}
