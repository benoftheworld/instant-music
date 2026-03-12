import VolumeControl from '@/components/game/VolumeControl';
import { Alert } from '@/components/ui';
import type { User } from '@/types';
import type { TabId } from '@/hooks/pages/useProfilePage';

function SectionTitle({ icon, title }: { icon: string; title: string }) {
  return (
    <h2 className="text-xl font-bold text-dark flex items-center gap-2">
      <span>{icon}</span>
      {title}
    </h2>
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

interface PasswordData {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

interface PasswordStrength {
  score: number;
  label: string;
  colorClass: string;
}

interface Props {
  activeTab: TabId;
  user: User;
  // Profile tab
  message: { type: 'success' | 'error'; text: string } | null;
  loading: boolean;
  avatarFile: File | null;
  avatarPreview: string | null;
  handleAvatarChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleProfileUpdate: (e: React.FormEvent) => void;
  // Security tab
  passwordData: PasswordData;
  setPasswordData: React.Dispatch<React.SetStateAction<PasswordData>>;
  showPasswords: { old: boolean; new: boolean; confirm: boolean };
  setShowPasswords: React.Dispatch<React.SetStateAction<{ old: boolean; new: boolean; confirm: boolean }>>;
  passwordMessage: { type: 'success' | 'error'; text: string } | null;
  handlePasswordChange: (e: React.FormEvent) => void;
  handleExportData: () => void;
  handleDeleteAccount: () => void;
  showDeleteZone: boolean;
  setShowDeleteZone: React.Dispatch<React.SetStateAction<boolean>>;
  deleteConfirmText: string;
  setDeleteConfirmText: React.Dispatch<React.SetStateAction<string>>;
  passwordStrength: PasswordStrength;
  confirmMismatch: boolean;
}

export default function ProfileSettings({
  activeTab,
  user,
  message,
  loading,
  avatarFile,
  avatarPreview,
  handleAvatarChange,
  handleProfileUpdate,
  passwordData,
  setPasswordData,
  showPasswords,
  setShowPasswords,
  passwordMessage,
  handlePasswordChange,
  handleExportData,
  handleDeleteAccount,
  showDeleteZone,
  setShowDeleteZone,
  deleteConfirmText,
  setDeleteConfirmText,
  passwordStrength,
  confirmMismatch,
}: Props) {
  return (
    <>
      {/* ── Profile Tab ──────────────────────────────────────────────────────── */}
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

      {/* ── Security Tab ─────────────────────────────────────────────────────── */}
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
    </>
  );
}
