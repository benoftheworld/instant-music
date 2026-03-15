import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useLogin } from '@/hooks/useAuth';
import { Button, Alert, FormField } from '@/components/ui';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const loginMutation = useLogin();
  const location = useLocation();
  const passwordResetSuccess = (location.state as { passwordResetSuccess?: boolean } | null)?.passwordResetSuccess;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loginMutation.mutate({ username, password });
  };

  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-md mx-auto card">
        <h1 className="text-3xl font-bold mb-6 text-center">Connexion</h1>

        {passwordResetSuccess && (
          <Alert variant="success" className="mb-4">
            Mot de passe réinitialisé avec succès. Vous pouvez vous connecter.
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <FormField
            label="Identifiant (email ou pseudonyme)"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            placeholder="Ex : monpseudo ou email@exemple.com"
          />

          <FormField
            label="Mot de passe"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            labelRight={
              <Link to="/forgot-password" className="text-sm text-primary-600 hover:underline">
                Mot de passe oublié ?
              </Link>
            }
            placeholder="Ex: MonMotDePasse123!"
          />

          {loginMutation.isError && (
            <Alert variant="error">Identifiants invalides</Alert>
          )}

          <Button type="submit" loading={loginMutation.isPending} className="w-full">
            Se connecter
          </Button>
        </form>

        <p className="text-center mt-4 text-gray-600">
          Pas encore de compte ?{' '}
          <Link to="/register" className="text-primary-600 hover:underline">
            Inscrivez-vous
          </Link>
        </p>
      </div>
    </div>
  );
}
