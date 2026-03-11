import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { api, getMediaUrl } from '@/services/api';
import { authService } from '@/services/authService';
import { achievementService } from '@/services/achievementService';
import { statsService } from '@/services/statsService';
import type { Achievement, UserDetailedStats } from '@/types';

interface PasswordData {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export type TabId = 'stats' | 'achievements' | 'profile' | 'security';

export function getPasswordStrength(password: string): { score: number; label: string; colorClass: string } {
  if (!password) return { score: 0, label: '', colorClass: '' };
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  if (score <= 1) return { score, label: 'Faible', colorClass: 'bg-red-500' };
  if (score <= 3) return { score, label: 'Moyen', colorClass: 'bg-yellow-500' };
  return { score, label: 'Fort', colorClass: 'bg-green-500' };
}

export function useProfilePage() {
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<TabId>('stats');
  const [achievementFilter, setAchievementFilter] = useState<'all' | 'unlocked' | 'locked'>('all');

  const [passwordData, setPasswordData] = useState<PasswordData>({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [showPasswords, setShowPasswords] = useState({ old: false, new: false, confirm: false });

  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [passwordMessage, setPasswordMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const { data: achievements = [], isLoading: achievementsLoading } = useQuery<Achievement[]>({
    queryKey: ['profile', 'achievements'],
    queryFn: () => achievementService.getAll(),
    staleTime: 60_000,
  });

  const { data: detailedStats = null } = useQuery<UserDetailedStats | null>({
    queryKey: ['profile', 'stats'],
    queryFn: () => statsService.getMyStats(),
    staleTime: 60_000,
  });

  const [showDeleteZone, setShowDeleteZone] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');

  useEffect(() => {
    if (user) {
      setAvatarPreview(getMediaUrl(user.avatar) || null);
    }
  }, [user]);

  useEffect(() => {
    const refreshUser = async () => {
      try {
        const fresh = await authService.getCurrentUser();
        updateUser(fresh);
      } catch (err) {
        console.error('Failed to refresh user data:', err);
      }
    };
    refreshUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAvatarFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setAvatarPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      const formData = new FormData();
      if (avatarFile) formData.append('avatar', avatarFile);
      const response = await api.patch('/users/me/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      updateUser(response.data);
      setMessage({ type: 'success', text: 'Profil mis à jour avec succès !' });
      setAvatarFile(null);
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } } };
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Erreur lors de la mise à jour du profil',
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage(null);
    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordMessage({ type: 'error', text: 'Les mots de passe ne correspondent pas' });
      return;
    }
    if (passwordData.new_password.length < 8) {
      setPasswordMessage({ type: 'error', text: 'Le mot de passe doit contenir au moins 8 caractères' });
      return;
    }
    setLoading(true);
    try {
      await api.post('/users/change_password/', {
        old_password: passwordData.old_password,
        new_password: passwordData.new_password,
      });
      setPasswordMessage({ type: 'success', text: 'Mot de passe modifié avec succès !' });
      setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
      setShowPasswords({ old: false, new: false, confirm: false });
    } catch (error) {
      const err = error as { response?: { data?: { old_password?: string; detail?: string } } };
      setPasswordMessage({
        type: 'error',
        text:
          err.response?.data?.old_password ||
          err.response?.data?.detail ||
          'Erreur lors du changement de mot de passe',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = async () => {
    try {
      const response = await api.get('/users/export_data/', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'mes-donnees-instantmusic.json');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export data error:', error);
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await api.delete('/users/delete_account/');
      await authService.logout();
      logout();
      navigate('/login');
    } catch (error) {
      console.error('Delete account error:', error);
      setDeleteConfirmText('');
      setShowDeleteZone(false);
    }
  };

  const getAchievementProgress = (achievement: Achievement): number => {
    if (achievement.unlocked || !user) return 100;
    const val = achievement.condition_value;
    switch (achievement.condition_type) {
      case 'games_played': return Math.min(99, Math.floor((user.total_games_played / val) * 100));
      case 'wins': return Math.min(99, Math.floor((user.total_wins / val) * 100));
      case 'points': return Math.min(99, Math.floor((user.total_points / val) * 100));
      default: return 0;
    }
  };

  const getAchievementProgressLabel = (achievement: Achievement): string => {
    if (!user || achievement.unlocked) return '';
    switch (achievement.condition_type) {
      case 'games_played': return `${user.total_games_played}/${achievement.condition_value}`;
      case 'wins': return `${user.total_wins}/${achievement.condition_value}`;
      case 'points': return `${user.total_points}/${achievement.condition_value}`;
      default: return '';
    }
  };

  const filteredAchievements = achievements.filter((a) => {
    if (achievementFilter === 'unlocked') return a.unlocked;
    if (achievementFilter === 'locked') return !a.unlocked;
    return true;
  });

  const unlockedCount = achievements.filter((a) => a.unlocked).length;
  const passwordStrength = getPasswordStrength(passwordData.new_password);
  const confirmMismatch =
    passwordData.confirm_password !== '' &&
    passwordData.new_password !== passwordData.confirm_password;

  return {
    user,
    activeTab,
    setActiveTab,
    achievementFilter,
    setAchievementFilter,
    passwordData,
    setPasswordData,
    showPasswords,
    setShowPasswords,
    avatarFile,
    avatarPreview,
    loading,
    message,
    passwordMessage,
    achievements,
    achievementsLoading,
    detailedStats,
    showDeleteZone,
    setShowDeleteZone,
    deleteConfirmText,
    setDeleteConfirmText,
    handleAvatarChange,
    handleProfileUpdate,
    handlePasswordChange,
    handleExportData,
    handleDeleteAccount,
    getAchievementProgress,
    getAchievementProgressLabel,
    filteredAchievements,
    unlockedCount,
    passwordStrength,
    confirmMismatch,
  };
}
