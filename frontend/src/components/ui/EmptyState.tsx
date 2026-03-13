import type { ReactNode } from 'react';

interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export default function EmptyState({ icon, title, description, action, className = '' }: EmptyStateProps) {
  return (
    <div className={`text-center py-12 ${className}`}>
      {icon && <div className="text-5xl mb-4">{icon}</div>}
      <h3 className="text-lg font-bold text-dark mb-1">{title}</h3>
      {description && <p className="text-gray-500 text-sm mb-4">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
