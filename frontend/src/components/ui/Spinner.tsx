import type { ReactNode } from 'react';

type SpinnerSize = 'sm' | 'md' | 'lg';

const sizeClasses: Record<SpinnerSize, string> = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-b-2',
  lg: 'h-12 w-12 border-b-3',
};

interface SpinnerProps {
  size?: SpinnerSize;
  className?: string;
}

export function Spinner({ size = 'md', className = '' }: SpinnerProps) {
  return (
    <div
      className={`inline-block animate-spin rounded-full border-primary-600 ${sizeClasses[size]} ${className}`}
      role="status"
      aria-label="Chargement"
    />
  );
}

interface LoadingStateProps {
  message?: string;
  size?: SpinnerSize;
  children?: ReactNode;
}

export function LoadingState({ message = 'Chargement...', size = 'md', children }: LoadingStateProps) {
  return (
    <div className="text-center py-8">
      <Spinner size={size} />
      {message && <p className="mt-2 text-gray-600">{message}</p>}
      {children}
    </div>
  );
}
