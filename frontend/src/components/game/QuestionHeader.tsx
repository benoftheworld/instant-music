import type React from 'react';

export function QuestionHeader({
  icon,
  title,
  subtitle,
  badge,
  audioStatus,
  gradientFrom = 'from-primary-600',
  gradientTo = 'to-primary-400',
}: {
  icon: string;
  title: string;
  subtitle?: string;
  badge?: React.ReactNode;
  audioStatus?: React.ReactNode;
  gradientFrom?: string;
  gradientTo?: string;
}) {
  return (
    <div className="bg-gradient-to-r from-primary-600 to-primary-500 rounded-t-2xl px-6 py-3 flex items-center justify-between shrink-0 mb-4 md:mb-6">
      <div className="flex items-center gap-3">
        <div className={`w-11 h-11 md:w-12 md:h-12 shrink-0 rounded-lg bg-gradient-to-br ${gradientFrom} ${gradientTo} flex items-center justify-center shadow`}>
          <span className="text-xl md:text-2xl">{icon}</span>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">{title}</h2>
          {subtitle && (
            <p className="text-white/70 text-xs mt-0.5 truncate">{subtitle}</p>
          )}
          {badge}
        </div>
      </div>
      {audioStatus && (
        <div className="flex items-center gap-2 shrink-0 ml-3">{audioStatus}</div>
      )}
    </div>
  );
}
