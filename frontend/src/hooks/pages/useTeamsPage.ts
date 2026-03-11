import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { teamService } from '@/services/socialService';
import { getApiErrorMessage } from '@/utils/apiError';
import { useAuthStore } from '@/store/authStore';
import type { Team } from '@/types';

export function useTeamsPage() {
  const user = useAuthStore((state) => state.user);
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'browse' | 'create'>('browse');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Create form
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamDescription, setNewTeamDescription] = useState('');
  const [creating, setCreating] = useState(false);

  const { data: allTeams = [], isLoading: loading } = useQuery<Team[]>({
    queryKey: ['teams', 'browse'],
    queryFn: async () => {
      const allData = await teamService.browseTeams();
      return Array.isArray(allData) ? allData : (allData as any)?.results || [];
    },
    staleTime: 30_000,
  });

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTeamName.trim()) return;

    setCreating(true);
    try {
      const team = await teamService.createTeam({
        name: newTeamName,
        description: newTeamDescription,
      });
      setNewTeamName('');
      setNewTeamDescription('');
      setMessage({ type: 'success', text: `Équipe "${team.name}" créée !` });
      navigate(`/teams/${team.id}`);
    } catch (err: unknown) {
      setMessage({ type: 'error', text: getApiErrorMessage(err, 'Erreur lors de la création') });
    } finally {
      setCreating(false);
    }
  };

  const handleJoinTeam = async (teamId: string) => {
    try {
      await teamService.joinTeam(teamId);
      setMessage({ type: 'success', text: `Demande d'adhésion envoyée.` });
    } catch (err: unknown) {
      setMessage({ type: 'error', text: getApiErrorMessage(err, 'Erreur') });
    }
  };

  const isInTeam = (teamId: string) => {
    if (!user) return false;
    const t = allTeams.find((tt) => tt.id === teamId);
    if (!t) return false;
    return (t.members_list || []).some((m) => m.user.id === user.id);
  };

  return {
    user,
    navigate,
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
  };
}
