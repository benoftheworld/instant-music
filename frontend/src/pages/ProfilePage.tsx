import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { api, getMediaUrl } from '@/services/api';
import { authService } from '@/services/authService';
import { achievementService } from '@/services/achievementService';
import { statsService } from '@/services/statsService';
import VolumeControl from '@/components/game/VolumeControl';
import { Alert } from '@/components/ui';
import { StatCard, MiniStat } from '@/components/ui/StatCard';
import type { Achievement, UserDetailedStats } from '@/types';

interface PasswordData {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

type TabId = 'stats' | 'achievements' | 'profile' | 'security';

const TABS: { id: TabId; label: string; icon: string }[] = [
  { id: 'stats', label: 'Statistiques', icon: '📊' },
  { id: 'achievements', label: 'Succès', icon: '🏆' },
  { id: 'profile', label: 'Profil', icon: '👤' },
  { id: 'security', label: 'Sécurité', icon: '🔒' },
];

const ACHIEVEMENT_ICONS: Record<string, string> = {
  games_played: '🎮',
  wins: '🏆',
  points: '⭐',
  perfect_round: '💯',
  win_streak: '🔥',
};

function getAchievementIcon(conditionType: string): string {
  return ACHIEVEMENT_ICONS[conditionType] ?? '🎵';
}

function getPasswordStrength(password: string): { score: number; label: string; colorClass: string } {
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

// ── Sub-components ──────────────────────────────────────────────────────────

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

function PasswordField({
  label,
  value,
  show,
  onToggle,
  onChange,
  placeholder,
  minLength,
  error,
}: {
  label: string;
  value: string;
  show: boolean;
  onToggle: () => void;
  onChange: (v: string) => void;
  placeholder: string;
  minLength?: number;
  error?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-semibold text-gray-700 mb-1.5">{label}</label>
      <div className="relative">
        <input
          type={show ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className={`input pr-11 ${error ? 'border-red-400 focus:ring-red-400 focus:border-red-400' : ''}`}
          placeholder={placeholder}
          required
          minLength={minLength}
        />
        <button
          type="button"
          onClick={onToggle}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
          tabIndex={-1}
          aria-label={show ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
        >
          {show ? (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          )}
        </button>
      </div>
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────

export default function ProfilePage() {
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

  if (!user) return null;

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

  return (
    <div className="min-h-screen bg-cream-100">
      <div className="max-w-5xl mx-auto px-4 py-8">

        {/* ── Profile Hero ─────────────────────────────────────────────────── */}
        <div className="card mb-6">
          <div className="flex flex-col sm:flex-row items-center gap-6">
            {/* Avatar */}
            <div className="w-24 h-24 rounded-full overflow-hidden ring-4 ring-primary-200 shadow-md flex-shrink-0">
              {avatarPreview ? (
                <img src={avatarPreview} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full bg-primary-100 flex items-center justify-center">
                  <span className="text-primary-500 text-4xl font-bold select-none">
                    {user.username.charAt(0).toUpperCase()}
                  </span>
                </div>
              )}
            </div>

            {/* Identity */}
            <div className="flex-1 text-center sm:text-left">
              <h1 className="text-3xl font-bold text-dark">{user.username}</h1>
              <p className="text-gray-500 text-sm mt-1">
                Membre depuis{' '}
                {new Date(user.created_at).toLocaleDateString('fr-FR', {
                  month: 'long',
                  year: 'numeric',
                })}
              </p>
              <div className="flex flex-wrap justify-center sm:justify-start gap-2 mt-3">
                <span className="flex items-center gap-1.5 text-sm bg-white px-3 py-1 rounded-full border border-cream-300 shadow-sm">
                  <span className="font-bold text-primary-600">{user.total_games_played}</span>
                  <span className="text-gray-500">parties</span>
                </span>
                <span className="flex items-center gap-1.5 text-sm bg-white px-3 py-1 rounded-full border border-cream-300 shadow-sm">
                  <span className="font-bold text-green-600">{user.total_wins}</span>
                  <span className="text-gray-500">victoires</span>
                </span>
                <span className="flex items-center gap-1.5 text-sm bg-white px-3 py-1 rounded-full border border-cream-300 shadow-sm">
                  <span className="font-bold text-primary-600">{user.total_points}</span>
                  <span className="text-gray-500">points</span>
                </span>
                {user.coins_balance !== undefined && (
                  <span className="flex items-center gap-1.5 text-sm bg-primary-50 px-3 py-1 rounded-full border border-primary-200">
                    <span>🪙</span>
                    <span className="font-bold text-primary-700">{user.coins_balance}</span>
                  </span>
                )}
              </div>
            </div>

            {/* Achievements quick access */}
            {detailedStats && (
              <button
                onClick={() => setActiveTab('achievements')}
                className="flex-shrink-0 text-center bg-primary-50 hover:bg-primary-100 rounded-xl p-4 border border-primary-200 transition-colors"
              >
                <div className="text-3xl mb-1">🏆</div>
                <div className="text-xl font-bold text-primary-700">
                  {detailedStats.achievements_unlocked}/{detailedStats.achievements_total}
                </div>
                <div className="text-xs text-gray-500 mt-0.5">Succès</div>
              </button>
            )}
          </div>
        </div>

        {/* ── Tab Navigation ───────────────────────────────────────────────── */}
        <div className="flex bg-white rounded-xl shadow-sm border border-cream-300 p-1 mb-6 gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-2 rounded-lg text-sm font-semibold transition-all ${
                activeTab === tab.id
                  ? 'bg-primary-500 text-white shadow-sm'
                  : 'text-dark-400 hover:bg-cream-100'
              }`}
            >
              <span className="text-base">{tab.icon}</span>
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* ── Statistics Tab ───────────────────────────────────────────────── */}
        {activeTab === 'stats' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard icon="🎮" label="Parties jouées" value={user.total_games_played} textColor="text-primary-600" bgClass="bg-primary-50 border-primary-200" />
              <StatCard icon="🏆" label="Victoires" value={user.total_wins} textColor="text-primary-600" bgClass="bg-primary-50 border-primary-200" />
              <StatCard icon="📈" label="Taux de victoire" value={`${(user.win_rate ?? 0).toFixed(1)}%`} textColor="text-primary-600" bgClass="bg-primary-50 border-primary-200" />
              <StatCard icon="⭐" label="Points totaux" value={user.total_points} textColor="text-primary-600" bgClass="bg-primary-50 border-primary-200" />
            </div>

            {detailedStats ? (
              <div className="card space-y-6">
                <SectionTitle icon="🎯" title="Performance" />
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
        )}

        {/* ── Achievements Tab ─────────────────────────────────────────────── */}
        {activeTab === 'achievements' && (
          <div className="card">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <SectionTitle icon="🏆" title={`Succès (${unlockedCount}/${achievements.length})`} />
              <div className="flex gap-2">
                {(
                  [
                    { id: 'all', label: 'Tous' },
                    { id: 'unlocked', label: '✅ Débloqués' },
                    { id: 'locked', label: '🔒 Verrouillés' },
                  ] as const
                ).map((f) => (
                  <button
                    key={f.id}
                    onClick={() => setAchievementFilter(f.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      achievementFilter === f.id
                        ? 'bg-primary-500 text-white'
                        : 'bg-cream-100 text-gray-600 hover:bg-cream-200'
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            {achievementsLoading ? (
              <div className="text-center py-12 text-gray-400">
                <div className="text-4xl mb-3">⏳</div>
                <p>Chargement des succès…</p>
              </div>
            ) : filteredAchievements.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <div className="text-4xl mb-3">🏅</div>
                <p>Aucun succès dans cette catégorie</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredAchievements.map((achievement) => {
                  const progress = getAchievementProgress(achievement);
                  const progressLabel = getAchievementProgressLabel(achievement);
                  return (
                    <div
                      key={achievement.id}
                      className={`rounded-xl p-4 border-2 transition-all ${
                        achievement.unlocked
                          ? 'border-yellow-300 bg-gradient-to-br from-yellow-50 to-amber-50 shadow-sm'
                          : 'border-gray-200 bg-gray-50'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`text-3xl flex-shrink-0 ${achievement.unlocked ? '' : 'grayscale opacity-50'}`}>
                          {getAchievementIcon(achievement.condition_type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <h3
                              className={`font-bold text-sm leading-tight ${
                                achievement.unlocked ? 'text-yellow-800' : 'text-gray-500'
                              }`}
                            >
                              {achievement.name}
                            </h3>
                            {achievement.unlocked && (
                              <svg className="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                            )}
                          </div>
                          <p className="text-xs text-gray-400 mt-0.5 leading-relaxed">{achievement.description}</p>
                          <div className="flex items-center justify-between mt-2">
                            <span
                              className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                                achievement.unlocked
                                  ? 'bg-yellow-200 text-yellow-800'
                                  : 'bg-gray-200 text-gray-500'
                              }`}
                            >
                              {achievement.points} pts
                            </span>
                            {achievement.unlocked && achievement.unlocked_at ? (
                              <span className="text-xs text-gray-400">
                                {new Date(achievement.unlocked_at).toLocaleDateString('fr-FR')}
                              </span>
                            ) : progressLabel ? (
                              <span className="text-xs text-gray-400">{progressLabel}</span>
                            ) : null}
                          </div>
                          {!achievement.unlocked && progress > 0 && (
                            <div className="mt-2 h-1.5 rounded-full bg-gray-200 overflow-hidden">
                              <div
                                className="h-full rounded-full bg-primary-400 transition-all"
                                style={{ width: `${progress}%` }}
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ── Profile Tab ──────────────────────────────────────────────────── */}
        {activeTab === 'profile' && (
          <div className="space-y-6">
            <div className="card">
              <SectionTitle icon="👤" title="Informations du profil" />
              {message && (
                <div className="mt-4">
                  <Alert variant={message.type}>{message.text}</Alert>
                </div>
              )}
              <form onSubmit={handleProfileUpdate} className="space-y-5 mt-5">
                {/* Avatar Upload */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    Photo de profil
                  </label>
                  <div className="flex items-center gap-5">
                    <div className="w-20 h-20 rounded-full overflow-hidden ring-4 ring-primary-200 flex-shrink-0 shadow">
                      {avatarPreview ? (
                        <img src={avatarPreview} alt="Avatar" className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full bg-primary-100 flex items-center justify-center">
                          <span className="text-primary-500 text-3xl font-bold">
                            {user.username.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="flex-1">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleAvatarChange}
                        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 cursor-pointer"
                      />
                      <p className="text-xs text-gray-400 mt-1.5">PNG, JPG, GIF jusqu'à 10 Mo</p>
                    </div>
                  </div>
                </div>

                {/* Username (read-only) */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                    Nom d'utilisateur
                  </label>
                  <input
                    type="text"
                    value={user.username}
                    disabled
                    className="input bg-cream-100 cursor-not-allowed text-gray-500"
                  />
                  <p className="text-xs text-gray-400 mt-1">Le nom d'utilisateur ne peut pas être modifié</p>
                </div>

                {/* Email (read-only) */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                    Adresse e-mail
                  </label>
                  <input
                    type="email"
                    value={user.email}
                    disabled
                    className="input bg-cream-100 cursor-not-allowed text-gray-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading || !avatarFile}
                  className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Enregistrement…' : 'Enregistrer la photo de profil'}
                </button>
              </form>
            </div>

            {/* Sound Settings */}
            <VolumeControl variant="card" />
          </div>
        )}

        {/* ── Security Tab ─────────────────────────────────────────────────── */}
        {activeTab === 'security' && (
          <div className="space-y-6">
            {/* Password Change */}
            <div className="card">
              <SectionTitle icon="🔑" title="Changer le mot de passe" />
              {passwordMessage && (
                <div className="mt-4">
                  <Alert variant={passwordMessage.type}>{passwordMessage.text}</Alert>
                </div>
              )}
              <form onSubmit={handlePasswordChange} className="space-y-4 mt-5">
                <PasswordField
                  label="Mot de passe actuel"
                  value={passwordData.old_password}
                  show={showPasswords.old}
                  onToggle={() => setShowPasswords((s) => ({ ...s, old: !s.old }))}
                  onChange={(v) => setPasswordData((d) => ({ ...d, old_password: v }))}
                  placeholder="Votre mot de passe actuel"
                />

                <PasswordField
                  label="Nouveau mot de passe"
                  value={passwordData.new_password}
                  show={showPasswords.new}
                  onToggle={() => setShowPasswords((s) => ({ ...s, new: !s.new }))}
                  onChange={(v) => setPasswordData((d) => ({ ...d, new_password: v }))}
                  placeholder="Votre nouveau mot de passe"
                  minLength={8}
                />

                {/* Strength meter */}
                {passwordData.new_password && (
                  <div className="-mt-2 pb-1">
                    <div className="flex gap-1 h-1.5">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <div
                          key={i}
                          className={`flex-1 rounded-full transition-all ${
                            i <= passwordStrength.score ? passwordStrength.colorClass : 'bg-gray-200'
                          }`}
                        />
                      ))}
                    </div>
                    {passwordStrength.label && (
                      <p className="text-xs text-gray-500 mt-1">
                        Force : <span className="font-semibold">{passwordStrength.label}</span>
                      </p>
                    )}
                  </div>
                )}

                <PasswordField
                  label="Confirmer le nouveau mot de passe"
                  value={passwordData.confirm_password}
                  show={showPasswords.confirm}
                  onToggle={() => setShowPasswords((s) => ({ ...s, confirm: !s.confirm }))}
                  onChange={(v) => setPasswordData((d) => ({ ...d, confirm_password: v }))}
                  placeholder="Répétez votre nouveau mot de passe"
                  error={confirmMismatch ? 'Les mots de passe ne correspondent pas' : undefined}
                />

                <button type="submit" disabled={loading} className="btn-primary w-full mt-2">
                  {loading ? 'Modification…' : 'Changer le mot de passe'}
                </button>
                <div className="bg-primary-50 border border-primary-200 rounded-lg p-3 text-sm text-primary-700">
                  Après le changement, vous restez connecté sur cet appareil.
                </div>
              </form>
            </div>

            {/* My Data */}
            <div className="card">
              <SectionTitle icon="💾" title="Mes données" />
              <p className="text-sm text-gray-500 mt-2 mb-4">
                Téléchargez une copie de toutes vos données personnelles au format JSON
                (RGPD — droit à la portabilité, art. 20).
              </p>
              <button onClick={handleExportData} className="btn-secondary text-sm">
                ⬇️ Télécharger mes données (JSON)
              </button>
            </div>

            {/* Danger Zone */}
            <div
              className={`rounded-xl border-2 p-6 transition-all ${
                showDeleteZone ? 'border-red-400 bg-red-50' : 'border-red-200 bg-red-50/50'
              }`}
            >
              <button
                onClick={() => setShowDeleteZone((v) => !v)}
                className="w-full flex items-center justify-between text-left"
              >
                <h2 className="text-lg font-bold text-red-700 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Zone dangereuse — Supprimer mon compte
                </h2>
                <svg
                  className={`w-5 h-5 text-red-500 transition-transform ${showDeleteZone ? 'rotate-180' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {showDeleteZone && (
                <div className="mt-4 space-y-3">
                  <p className="text-sm text-red-600">
                    Cette action est <strong>irréversible</strong>. Toutes vos données seront définitivement
                    supprimées : profil, statistiques, historique de parties et succès.
                  </p>
                  <p className="text-sm text-red-700 font-medium">
                    Tapez{' '}
                    <code className="bg-red-100 px-1.5 py-0.5 rounded font-mono text-red-800">
                      SUPPRIMER
                    </code>{' '}
                    pour confirmer :
                  </p>
                  <input
                    type="text"
                    value={deleteConfirmText}
                    onChange={(e) => setDeleteConfirmText(e.target.value)}
                    className="input border-red-300 focus:ring-red-400 focus:border-red-400"
                    placeholder="SUPPRIMER"
                  />
                  <div className="flex gap-3 pt-1">
                    <button
                      onClick={() => {
                        setShowDeleteZone(false);
                        setDeleteConfirmText('');
                      }}
                      className="btn-secondary flex-1 text-sm"
                    >
                      Annuler
                    </button>
                    <button
                      onClick={handleDeleteAccount}
                      disabled={deleteConfirmText !== 'SUPPRIMER'}
                      className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded-md transition-colors text-sm"
                    >
                      Supprimer définitivement
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
