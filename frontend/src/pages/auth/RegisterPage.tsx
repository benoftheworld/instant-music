import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useRegister } from '@/hooks/useAuth';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password2: '',
    accept_privacy_policy: false,
  });
  const registerMutation = useRegister();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    registerMutation.mutate(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({
      ...formData,
      [e.target.name]: value,
    });
  };

  return (
    <div className="container mx-auto px-4 py-16">
      <div className="max-w-md mx-auto card">
        <h1 className="text-3xl font-bold mb-6 text-center">Inscription</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Nom d'utilisateur
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              className="input"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="input"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Mot de passe
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="input"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Confirmer le mot de passe
            </label>
            <input
              type="password"
              name="password2"
              value={formData.password2}
              onChange={handleChange}
              className="input"
              required
            />
          </div>

          <div className="flex items-start gap-2">
            <input
              type="checkbox"
              id="accept_privacy_policy"
              name="accept_privacy_policy"
              checked={formData.accept_privacy_policy}
              onChange={handleChange}
              className="mt-1"
              required
            />
            <label htmlFor="accept_privacy_policy" className="text-sm text-gray-600">
              J'accepte la{' '}
              <a href="/privacy" className="text-primary-600 hover:underline" target="_blank" rel="noopener noreferrer">
                politique de confidentialité
              </a>
            </label>
          </div>

          {registerMutation.isError && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              <p className="font-semibold">Erreur lors de l'inscription</p>
              <div className="mt-2 text-sm">
                {(() => {
                  const err = (registerMutation.error as any)?.response?.data;
                  if (!err) return <div>Erreur inconnue</div>;
                  if (typeof err === 'string') return <div>{err}</div>;
                  // err is likely an object with field arrays
                  return Object.entries(err).map(([k, v]) => (
                    <div key={k}>
                      <strong>{k}:</strong> {Array.isArray(v) ? v.join(' ') : String(v)}
                    </div>
                  ));
                })()}
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={registerMutation.isPending}
            className="btn-primary w-full"
          >
            {registerMutation.isPending ? 'Inscription...' : 'S\'inscrire'}
          </button>
        </form>

        <p className="text-center mt-4 text-gray-600">
          Déjà un compte ?{' '}
          <Link to="/login" className="text-primary-600 hover:underline">
            Connectez-vous
          </Link>
        </p>
      </div>
    </div>
  );
}
