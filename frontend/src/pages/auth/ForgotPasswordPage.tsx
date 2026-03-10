import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authService } from '@/services/authService';
import { Button, Alert, FormField } from '@/components/ui';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await authService.requestPasswordReset(email);
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
              Si un compte existe avec cette adresse, un lien de réinitialisation vous a été envoyé.
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
              Saisissez votre adresse email. Si un compte associé existe, vous recevrez un lien de réinitialisation.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <FormField
                label="Adresse email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
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
