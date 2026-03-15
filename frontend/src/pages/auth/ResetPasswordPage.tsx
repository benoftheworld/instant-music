import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { authService } from '@/services/authService';
import { Button, Alert, PasswordInput, PasswordStrengthBar } from '@/components/ui';

export default function ResetPasswordPage() {
  const { uid, token } = useParams<{ uid: string; token: string }>();
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (newPassword !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas.');
      return;
    }

    if (!uid || !token) {
      setError('Lien invalide.');
      return;
    }

    setIsLoading(true);
    try {
      await authService.confirmPasswordReset(uid, token, newPassword);
      navigate('/login', { state: { passwordResetSuccess: true } });
    } catch {
      setError('Lien invalide ou expiré. Veuillez faire une nouvelle demande.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-md mx-auto card">
        <h1 className="text-3xl font-bold mb-6 text-center">
          Nouveau mot de passe
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <PasswordInput
              label="Nouveau mot de passe"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              autoComplete="new-password"
              placeholder="8+ car., majuscule, chiffre, symbole (ex: MonP@ss1)"
            />
            <PasswordStrengthBar password={newPassword} />
          </div>

          <PasswordInput
            label="Confirmer le mot de passe"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            autoComplete="new-password"
            placeholder="Répétez votre nouveau mot de passe"
          />

          <p className="text-xs text-gray-500 bg-gray-50 rounded p-2">
            💡 <strong>Conseil :</strong> utilisez un gestionnaire de mots de passe comme{' '}
            <a
              href="https://keepass.info"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:underline"
            >
              KeePass
            </a>{' '}
            pour générer et stocker un mot de passe sécurisé.
          </p>

          {error && <Alert variant="error">{error}</Alert>}

          <Button type="submit" loading={isLoading} className="w-full">
            Réinitialiser le mot de passe
          </Button>
        </form>
      </div>
    </div>
  );
}
