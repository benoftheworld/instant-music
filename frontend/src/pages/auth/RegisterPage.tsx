import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useRegister } from '@/hooks/useAuth';
import { userService } from '@/services/userService';
import { Button, Alert, FormField } from '@/components/ui';

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
    } catch {
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
    } catch {
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
          <FormField
            label="Nom d'utilisateur"
            type="text"
            name="username"
            value={formData.username}
            onChange={handleChange}
            onBlur={handleUsernameBlur}
            required
            error={usernameError ?? undefined}
            hint={usernameAvailable ? 'Pseudonyme disponible.' : checkingUsername ? 'Vérification...' : undefined}
          />

          <FormField
            label="Email"
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            onBlur={handleEmailBlur}
            required
            error={emailError ?? undefined}
            hint={emailAvailable ? 'Email disponible.' : checkingEmail ? 'Vérification...' : undefined}
          />

          <FormField
            label="Mot de passe"
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
          />

          <FormField
            label="Confirmer le mot de passe"
            type="password"
            name="password2"
            value={formData.password2}
            onChange={handleChange}
            required
          />

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
            <Alert variant="error">
              <p className="font-semibold">Erreur lors de l'inscription</p>
              <div className="mt-2 text-sm">
                {(() => {
                  const err = (registerMutation.error as any)?.response?.data;
                  if (!err) return <div>Erreur inconnue</div>;
                  if (typeof err === 'string') return <div>{err}</div>;
                  return Object.entries(err).map(([k, v]) => (
                    <div key={k}>
                      <strong>{k}:</strong> {Array.isArray(v) ? v.join(' ') : String(v)}
                    </div>
                  ));
                })()}
              </div>
            </Alert>
          )}

          <Button
            type="submit"
            loading={registerMutation.isPending}
            disabled={
              Boolean(usernameError) ||
              Boolean(emailError) ||
              usernameAvailable === false ||
              emailAvailable === false ||
              checkingUsername ||
              checkingEmail
            }
            className="w-full"
          >
            S'inscrire
          </Button>
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
