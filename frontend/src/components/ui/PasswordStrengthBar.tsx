import { getPasswordStrength } from '@/hooks/pages/useProfilePage';

interface PasswordStrengthBarProps {
  password: string;
}

/**
 * Barre de progression indiquant la force du mot de passe.
 */
export default function PasswordStrengthBar({ password }: PasswordStrengthBarProps) {
  if (!password) return null;
  const { score, label, colorClass } = getPasswordStrength(password);
  const segments = 5;

  return (
    <div aria-label={`Force du mot de passe : ${label}`}>
      <div className="flex gap-1 mt-1">
        {Array.from({ length: segments }).map((_, i) => (
          <div
            key={i}
            className={`h-1.5 flex-1 rounded-full transition-colors ${
              i < score ? colorClass : 'bg-gray-200'
            }`}
          />
        ))}
      </div>
      {label && (
        <p className="text-xs mt-1 text-gray-600">
          Force : <span className="font-medium">{label}</span>
        </p>
      )}
    </div>
  );
}
