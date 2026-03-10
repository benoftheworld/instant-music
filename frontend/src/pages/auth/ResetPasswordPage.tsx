import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { authService } from '@/services/authService';
import { Button, Alert, FormField } from '@/components/ui';

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
          <FormField
            label="Nouveau mot de passe"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            autoComplete="new-password"
          />

          <FormField
            label="Confirmer le mot de passe"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            autoComplete="new-password"
          />

          {error && <Alert variant="error">{error}</Alert>}

          <Button type="submit" loading={isLoading} className="w-full">
            Réinitialiser le mot de passe
          </Button>
        </form>
      </div>
    </div>
  );
}
