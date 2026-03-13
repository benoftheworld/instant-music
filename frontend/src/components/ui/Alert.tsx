import type { ReactNode } from 'react';

type AlertVariant = 'success' | 'error' | 'warning' | 'info';

interface AlertProps {
  variant: AlertVariant;
  children: ReactNode;
  icon?: ReactNode;
  className?: string;
  onClose?: () => void;
}

const variantConfig: Record<AlertVariant, { classes: string; defaultIcon: string }> = {
  success: {
    classes: 'bg-green-50 text-green-800 border border-green-200',
    defaultIcon: '✅',
  },
  error: {
    classes: 'bg-red-50 text-red-800 border border-red-200',
    defaultIcon: '❌',
  },
  warning: {
    classes: 'bg-yellow-50 text-yellow-800 border border-yellow-200',
    defaultIcon: '⚠️',
  },
  info: {
    classes: 'bg-blue-50 text-blue-800 border border-blue-200',
    defaultIcon: 'ℹ️',
  },
};

export default function Alert({ variant, children, icon, className = '', onClose }: AlertProps) {
  const config = variantConfig[variant];

  return (
    <div className={`flex items-start gap-2 p-3 rounded-lg text-sm ${config.classes} ${className}`} role="alert">
      <span className="flex-shrink-0">{icon ?? config.defaultIcon}</span>
      <span className="flex-1">{children}</span>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity"
          aria-label="Fermer"
        >
          ✕
        </button>
      )}
    </div>
  );
}
