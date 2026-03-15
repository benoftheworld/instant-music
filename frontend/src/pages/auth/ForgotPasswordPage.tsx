import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authService } from '@/services/authService';
import { Button, Alert, FormField } from '@/components/ui';

export default function ForgotPasswordPage() {
  const [username, setUsername] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await authService.requestPasswordReset(username);
    } finally {
      setIsLoading(false);
      setSubmitted(true);
    }
  };

  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-md mx-auto card">
        <h1 className="text-3xl font-bold mb-6 text-center">Mot de passe oublié</h1>

        {submitted ? (
          <div className="space-y-4">
            <Alert variant="success">
              Si un compte existe avec ce pseudonyme, un lien de réinitialisation vous a été envoyé par email.
            </Alert>
            <p className="text-center text-gray-600">
              <Link to="/login" className="text-primary-600 hover:underline">
                Retour à la connexion
              </Link>
            </p>
          </div>
        ) : (
          <>
            <p className="text-gray-600 mb-6">
              Saisissez votre pseudonyme. Si un compte associé existe, vous recevrez un lien de réinitialisation par email.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <FormField
                label="Pseudonyme"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                placeholder="Votre pseudonyme (ex : monpseudo)"
                maxLength={20}
              />

              <Button type="submit" loading={isLoading} className="w-full">
                Envoyer le lien
              </Button>
            </form>

            <p className="text-center mt-4 text-gray-600">
              <Link to="/login" className="text-primary-600 hover:underline">
                Retour à la connexion
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
