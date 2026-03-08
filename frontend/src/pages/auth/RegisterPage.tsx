import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useRegister } from '@/hooks/useAuth';
import { userService } from '@/services/userService';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password2: '',
    accept_privacy_policy: false,
  });
  const registerMutation = useRegister();

  const [usernameError, setUsernameError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [usernameAvailable, setUsernameAvailable] = useState<boolean | null>(null);
  const [checkingUsername, setCheckingUsername] = useState(false);
  const [emailAvailable, setEmailAvailable] = useState<boolean | null>(null);
  const [checkingEmail, setCheckingEmail] = useState(false);

  // Validation regex (as requested by user)
  const usernameRegex = /^[a-zA-Z0-9\-_']*$/;
  const emailRegex = /^((?!\.)[\w\-_.]*[^.])(@\w+)(\.\w+(\.\w+)?[^.\W])$/;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Final client-side checks
    if (usernameError || emailError) return;
    if (usernameAvailable === false) return;
    if (emailAvailable === false) return;

    registerMutation.mutate(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({
      ...formData,
      [e.target.name]: value,
    });

    // Inline validation
    if (e.target.name === 'username') {
      setUsernameAvailable(null);
      if (!usernameRegex.test(String(value))) {
        setUsernameError("Nom d'utilisateur invalide : caractères non autorisés.");
      } else {
        setUsernameError(null);
      }
    }

    if (e.target.name === 'email') {
      setEmailAvailable(null);
      if (!emailRegex.test(String(value))) {
        setEmailError('Email invalide : caractères non autorisés.');
      } else {
        setEmailError(null);
      }
    }
  };

  const handleUsernameBlur = async () => {
    const username = String(formData.username || '').trim();
    if (!username || usernameError) return;

    setCheckingUsername(true);
    try {
      const exists = await userService.usernameExists(username);
      setUsernameAvailable(!exists);
      if (exists) setUsernameError('Ce pseudonyme est déjà utilisé.');
    } catch (err) {
      // Ignore network errors here — backend will validate on submit
    } finally {
      setCheckingUsername(false);
    }
  };

  const handleEmailBlur = async () => {
    const email = String(formData.email || '').trim();
    if (!email || emailError) return;

    setCheckingEmail(true);
    try {
      const exists = await userService.emailExists(email);
      setEmailAvailable(!exists);
      if (exists) setEmailError('Cette adresse email est déjà utilisée.');
    } catch (err) {
      // Ignore network errors here — backend will validate on submit
    } finally {
      setCheckingEmail(false);
    }
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
              onBlur={handleUsernameBlur}
              className="input"
              required
            />
            {usernameError && (
              <p className="text-sm text-red-600 mt-1">{usernameError}</p>
            )}
            {usernameAvailable && (
              <p className="text-sm text-green-600 mt-1">Pseudonyme disponible.</p>
            )}
            {checkingUsername && (
              <p className="text-sm text-gray-500 mt-1">Vérification...</p>
            )}
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
              onBlur={handleEmailBlur}
              className="input"
              required
            />
            {emailError && (
              <p className="text-sm text-red-600 mt-1">{emailError}</p>
            )}
            {emailAvailable && (
              <p className="text-sm text-green-600 mt-1">Email disponible.</p>
            )}
            {checkingEmail && (
              <p className="text-sm text-gray-500 mt-1">Vérification...</p>
            )}
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
            disabled={
              registerMutation.isPending ||
              Boolean(usernameError) ||
              Boolean(emailError) ||
              usernameAvailable === false ||
              emailAvailable === false ||
              checkingUsername ||
              checkingEmail
            }
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
