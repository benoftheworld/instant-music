import { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import SpotifyConnection from '@/components/spotify/SpotifyConnection';
import { api } from '@/services/api';

interface ProfileData {
  bio: string;
  avatar: string | null;
}

interface PasswordData {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export default function ProfilePage() {
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);

  const [profileData, setProfileData] = useState<ProfileData>({
    bio: user?.bio || '',
    avatar: user?.avatar || null,
  });

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

  useEffect(() => {
    if (user) {
      setProfileData({
        bio: user.bio || '',
        avatar: user.avatar || null,
      });
      setAvatarPreview(user.avatar || null);
    }
  }, [user]);

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
      formData.append('bio', profileData.bio);
      
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
          </div>
        </div>

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

              {/* Bio */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Biographie
                </label>
                <textarea
                  value={profileData.bio}
                  onChange={(e) => setProfileData({ ...profileData, bio: e.target.value })}
                  className="input min-h-[100px] resize-y"
                  placeholder="Parlez-nous de vous..."
                  maxLength={500}
                />
                <p className="text-xs text-gray-500 mt-1">
                  {profileData.bio.length}/500 caractères
                </p>
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

        {/* Spotify Connection Section */}
        <SpotifyConnection />
      </div>
    </div>
  );
}
