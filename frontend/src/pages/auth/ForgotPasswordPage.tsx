import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authService } from '@/services/authService';

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
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
              Si un compte existe avec cette adresse, un lien de réinitialisation vous a été envoyé.
            </div>
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
              <div>
                <label className="block text-sm font-medium mb-1">
                  Adresse email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input"
                  required
                  autoComplete="email"
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary w-full"
              >
                {isLoading ? 'Envoi...' : 'Envoyer le lien'}
              </button>
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
