import { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { api, getMediaUrl } from '@/services/api';
import { authService } from '@/services/authService';
import { achievementService } from '@/services/achievementService';
import { statsService } from '@/services/achievementService';
import VolumeControl from '@/components/game/VolumeControl';
import type { Achievement, UserDetailedStats } from '@/types';

interface PasswordData {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export default function ProfilePage() {
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);

  const [passwordData, setPasswordData] = useState<PasswordData>({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });

  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [passwordMessage, setPasswordMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [achievementsLoading, setAchievementsLoading] = useState(true);
  const [detailedStats, setDetailedStats] = useState<UserDetailedStats | null>(null);

  useEffect(() => {
    if (user) {
      setAvatarPreview(getMediaUrl(user.avatar) || null);
    }
  }, [user]);

  // Fetch latest user stats on mount
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

    const fetchAchievements = async () => {
      try {
        setAchievementsLoading(true);
        const data = await achievementService.getAll();
        setAchievements(data);
      } catch (err) {
        console.error('Failed to load achievements:', err);
      } finally {
        setAchievementsLoading(false);
      }
    };
    fetchAchievements();

    const fetchStats = async () => {
      try {
        const data = await statsService.getMyStats();
        setDetailedStats(data);
      } catch (err) {
        console.error('Failed to load detailed stats:', err);
      }
    };
    fetchStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAvatarFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setAvatarPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const formData = new FormData();
      
      if (avatarFile) {
        formData.append('avatar', avatarFile);
      }

      const response = await api.patch('/users/me/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      updateUser(response.data);
      setMessage({ type: 'success', text: 'Profil mis à jour avec succès !' });
      setAvatarFile(null);
    } catch (error) {
      console.error('Profile update error:', error);
      const err = error as { response?: { data?: { detail?: string } } };
      setMessage({ 
        type: 'error', 
        text: err.response?.data?.detail || 'Erreur lors de la mise à jour du profil' 
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage(null);

    // Validation
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
      setPasswordData({
        old_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (error) {
      console.error('Password change error:', error);
      const err = error as { response?: { data?: { old_password?: string; detail?: string } } };
      setPasswordMessage({ 
        type: 'error', 
        text: err.response?.data?.old_password || err.response?.data?.detail || 'Erreur lors du changement de mot de passe' 
      });
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  const getAchievementIcon = (conditionType: string): string => {
    switch (conditionType) {
      case 'games_played': return '🎮';
      case 'wins': return '🏆';
      case 'points': return '⭐';
      case 'perfect_round': return '💯';
      case 'win_streak': return '🔥';
      default: return '🎵';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-2">Mon Profil</h1>
          <p className="text-gray-600">Gérez vos informations personnelles et vos préférences</p>
        </div>

        {/* Stats Overview Card */}
        <div className="card bg-gradient-to-r from-primary-50 to-purple-50">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-4xl font-bold text-primary-600 mb-1">
                {user.total_games_played}
              </div>
              <div className="text-sm text-gray-600 uppercase tracking-wide">Parties jouées</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-green-600 mb-1">
                {user.total_wins}
              </div>
              <div className="text-sm text-gray-600 uppercase tracking-wide">Victoires</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-yellow-600 mb-1">
                {(user.win_rate ?? 0).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600 uppercase tracking-wide">Taux de victoire</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary-800 mb-1">
                {user.total_points}
              </div>
              <div className="text-sm text-gray-600 uppercase tracking-wide">Points totaux</div>
            </div>
          </div>
        </div>

        {/* Detailed Stats */}
        {detailedStats && (
          <div className="card">
            <h2 className="text-2xl font-bold mb-4 flex items-center">
              <svg className="w-6 h-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Statistiques détaillées
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-blue-600">{detailedStats.avg_score_per_game.toFixed(0)}</div>
                <div className="text-xs text-gray-500 mt-1">Score moyen</div>
              </div>
              <div className="bg-green-50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-green-600">{detailedStats.best_score}</div>
                <div className="text-xs text-gray-500 mt-1">Meilleur score</div>
              </div>
              <div className="bg-purple-50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-purple-600">{detailedStats.accuracy.toFixed(1)}%</div>
                <div className="text-xs text-gray-500 mt-1">Précision</div>
              </div>
              <div className="bg-orange-50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-orange-600">{detailedStats.avg_response_time.toFixed(1)}s</div>
                <div className="text-xs text-gray-500 mt-1">Temps moyen</div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="bg-gray-50 rounded-lg p-3 flex items-center justify-between">
                <span className="text-sm text-gray-600">Réponses correctes</span>
                <span className="font-bold text-gray-800">{detailedStats.total_correct_answers}/{detailedStats.total_answers}</span>
              </div>
              <div className="bg-gray-50 rounded-lg p-3 flex items-center justify-between">
                <span className="text-sm text-gray-600">Succès débloqués</span>
                <span className="font-bold text-gray-800">{detailedStats.achievements_unlocked}/{detailedStats.achievements_total}</span>
              </div>
            </div>
          </div>
        )}

        {/* Achievements Section */}
        <div className="card">
          <h2 className="text-2xl font-bold mb-4 flex items-center">
            <svg className="w-6 h-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
            Succès ({Array.isArray(achievements) ? achievements.filter(a => a.unlocked).length : 0}/{Array.isArray(achievements) ? achievements.length : 0})
          </h2>
          
          {achievementsLoading ? (
            <div className="text-center py-8 text-gray-400">Chargement des succès...</div>
          ) : achievements.length === 0 ? (
            <div className="text-center py-8 text-gray-400">Aucun succès disponible</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {achievements.map((achievement) => (
                <div
                  key={achievement.id}
                  className={`p-4 rounded-xl border-2 transition-all ${
                    achievement.unlocked
                      ? 'border-yellow-400 bg-yellow-50 shadow-md'
                      : 'border-gray-200 bg-gray-50 opacity-60'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div className={`text-3xl flex-shrink-0 ${achievement.unlocked ? '' : 'grayscale'}`}>
                      {getAchievementIcon(achievement.condition_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className={`font-bold text-sm ${achievement.unlocked ? 'text-yellow-800' : 'text-gray-500'}`}>
                        {achievement.name}
                      </h3>
                      <p className="text-xs text-gray-500 mt-0.5">{achievement.description}</p>
                      <div className="flex items-center justify-between mt-2">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                          achievement.unlocked
                            ? 'bg-yellow-200 text-yellow-800'
                            : 'bg-gray-200 text-gray-500'
                        }`}>
                          {achievement.points} pts
                        </span>
                        {achievement.unlocked && achievement.unlocked_at && (
                          <span className="text-xs text-gray-400">
                            {new Date(achievement.unlocked_at).toLocaleDateString('fr-FR')}
                          </span>
                        )}
                      </div>
                    </div>
                    {achievement.unlocked && (
                      <div className="text-yellow-500 flex-shrink-0">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sound Settings */}
        <VolumeControl variant="card" />

        <div className="grid md:grid-cols-2 gap-6">
          {/* Profile Information Card */}
          <div className="card">
            <h2 className="text-2xl font-bold mb-4 flex items-center">
              <svg className="w-6 h-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              Informations du profil
            </h2>

            {message && (
              <div className={`mb-4 p-3 rounded-lg ${
                message.type === 'success' 
                  ? 'bg-green-50 text-green-800 border border-green-200' 
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}>
                {message.text}
              </div>
            )}

            <form onSubmit={handleProfileUpdate} className="space-y-4">
              {/* Avatar Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Photo de profil
                </label>
                <div className="flex items-center space-x-4">
                  <div className="w-20 h-20 rounded-full bg-gray-200 overflow-hidden flex-shrink-0">
                    {avatarPreview ? (
                      <img src={avatarPreview} alt="Avatar" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-400">
                        <svg className="w-10 h-10" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleAvatarChange}
                      className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
                    />
                    <p className="text-xs text-gray-500 mt-1">PNG, JPG jusqu'à 10MB</p>
                  </div>
                </div>
              </div>

              {/* Username (read-only) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nom d'utilisateur
                </label>
                <input
                  type="text"
                  value={user.username}
                  disabled
                  className="input bg-gray-100 cursor-not-allowed"
                />
                <p className="text-xs text-gray-500 mt-1">Le nom d'utilisateur ne peut pas être modifié</p>
              </div>

              {/* Email (read-only) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={user.email}
                  disabled
                  className="input bg-gray-100 cursor-not-allowed"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full"
              >
                {loading ? 'Enregistrement...' : 'Enregistrer les modifications'}
              </button>
            </form>
          </div>

          {/* Password Change Card */}
          <div className="card">
            <h2 className="text-2xl font-bold mb-4 flex items-center">
              <svg className="w-6 h-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Changer le mot de passe
            </h2>

            {passwordMessage && (
              <div className={`mb-4 p-3 rounded-lg ${
                passwordMessage.type === 'success' 
                  ? 'bg-green-50 text-green-800 border border-green-200' 
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}>
                {passwordMessage.text}
              </div>
            )}

            <form onSubmit={handlePasswordChange} className="space-y-4">
              {/* Old Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Mot de passe actuel
                </label>
                <input
                  type="password"
                  value={passwordData.old_password}
                  onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
                  className="input"
                  placeholder="Entrez votre mot de passe actuel"
                  required
                />
              </div>

              {/* New Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nouveau mot de passe
                </label>
                <input
                  type="password"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                  className="input"
                  placeholder="Entrez votre nouveau mot de passe"
                  required
                  minLength={8}
                />
                <p className="text-xs text-gray-500 mt-1">Minimum 8 caractères</p>
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Confirmer le nouveau mot de passe
                </label>
                <input
                  type="password"
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                  className="input"
                  placeholder="Confirmez votre nouveau mot de passe"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full"
              >
                {loading ? 'Modification...' : 'Changer le mot de passe'}
              </button>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
                <strong>Note :</strong> Après avoir changé votre mot de passe, vous resterez connecté sur cet appareil.
              </div>
            </form>
          </div>
        </div>

        {/* Delete Account Section */}
        <div className="card border-2 border-red-200 bg-red-50">
          <h2 className="text-2xl font-bold mb-4 flex items-center text-red-700">
            <svg className="w-6 h-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Supprimer mon compte
          </h2>
          <p className="text-sm text-red-600 mb-4">
            Cette action est irréversible. Toutes vos données seront définitivement supprimées : 
            profil, statistiques, historique de parties, amitiés et équipes.
          </p>
          <button
            onClick={() => {
              if (window.confirm('Êtes-vous sûr de vouloir supprimer votre compte ? Cette action est irréversible.')) {
                if (window.confirm('Dernière confirmation : toutes vos données seront définitivement perdues. Continuer ?')) {
                  api.delete('/users/delete_account/')
                    .then(() => {
                      window.location.href = '/';
                    })
                    .catch((err) => {
                      console.error('Delete account error:', err);
                      alert('Erreur lors de la suppression du compte');
                    });
                }
              }
            }}
            className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg transition-colors"
          >
            Supprimer définitivement mon compte
          </button>
        </div>

      </div>
    </div>
  );
}
