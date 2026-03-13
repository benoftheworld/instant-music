/**
 * AchievementToastManager
 *
 * S'abonne aux events `achievement_unlocked` du NotificationWebSocket
 * et affiche une pile de toasts animés en bas à droite.
 * À monter une seule fois à la racine de l'application.
 */
import { useEffect, useState, useCallback } from 'react';
import { notificationWS } from '@/services/notificationWebSocket';
import { useAuthStore } from '@/store/authStore';
import { getMediaUrl } from '@/services/api';

interface AchievementPayload {
  id: string;
  name: string;
  description: string;
  icon: string | null;
  points: number;
}

interface ToastEntry {
  key: string;
  achievement: AchievementPayload;
  /** true = glisse vers l'intérieur, false = glisse vers l'extérieur */
  visible: boolean;
}

const TOAST_DURATION_MS = 6000;
const LEAVE_DURATION_MS = 500;

export default function AchievementToastManager() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [toasts, setToasts] = useState<ToastEntry[]>([]);

  const dismiss = useCallback((key: string) => {
    // Déclenche l'animation de sortie
    setToasts((prev) =>
      prev.map((t) => (t.key === key ? { ...t, visible: false } : t))
    );
    // Supprime le toast après l'animation
    setTimeout(
      () => setToasts((prev) => prev.filter((t) => t.key !== key)),
      LEAVE_DURATION_MS
    );
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;

    const unsub = notificationWS.on('achievement_unlocked', (data) => {
      if (!data?.achievement) return;

      const key = `${data.achievement.id}-${Date.now()}`;
      const entry: ToastEntry = {
        key,
        achievement: data.achievement as AchievementPayload,
        visible: true,
      };

      setToasts((prev) => [...prev, entry]);

      // Auto-dismiss
      setTimeout(() => dismiss(key), TOAST_DURATION_MS);
    });

    return unsub;
  }, [isAuthenticated, dismiss]);

  if (toasts.length === 0) return null;

  return (
    <div
      aria-live="polite"
      aria-label="Notifications de succès"
      className="fixed bottom-6 right-4 z-[9999] flex flex-col gap-3 items-end pointer-events-none"
    >
      {toasts.map((toast) => (
        <AchievementToast
          key={toast.key}
          achievement={toast.achievement}
          visible={toast.visible}
          onDismiss={() => dismiss(toast.key)}
        />
      ))}
    </div>
  );
}

function AchievementToast({
  achievement,
  visible,
  onDismiss,
}: {
  achievement: AchievementPayload;
  visible: boolean;
  onDismiss: () => void;
}) {
  return (
    <div
      role="alert"
      className={[
        'pointer-events-auto w-80 max-w-[calc(100vw-2rem)]',
        'bg-dark border-2 border-yellow-500 rounded-xl shadow-2xl',
        'flex items-start gap-3 px-4 py-3',
        'transition-all duration-500',
        visible
          ? 'opacity-100 translate-x-0'
          : 'opacity-0 translate-x-12',
      ].join(' ')}
    >
      {/* Icône */}
      <div className="shrink-0 w-12 h-12 rounded-full bg-yellow-500/20 border border-yellow-500 flex items-center justify-center overflow-hidden">
        {achievement.icon ? (
          <img
            src={getMediaUrl(achievement.icon)}
            alt={achievement.name}
            className="w-8 h-8 object-contain"
          />
        ) : (
          <TrophyIcon />
        )}
      </div>

      {/* Texte */}
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-yellow-400 uppercase tracking-wide mb-0.5">
          Succès débloqué !
        </p>
        <p className="text-sm font-bold text-cream-100 leading-tight truncate">
          {achievement.name}
        </p>
        <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">
          {achievement.description}
        </p>
        <p className="text-xs text-yellow-500 font-semibold mt-1">
          +{achievement.points} pts
        </p>
      </div>

      {/* Bouton fermer */}
      <button
        onClick={onDismiss}
        aria-label="Fermer"
        className="shrink-0 text-gray-500 hover:text-gray-300 transition-colors mt-0.5"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>

      {/* Barre de progression */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 rounded-b-xl overflow-hidden">
        <div
          className={[
            'h-full bg-yellow-500',
            visible ? 'achievement-progress-bar' : '',
          ].join(' ')}
          style={
            visible
              ? ({
                  '--duration': `${6000}ms`,
                } as React.CSSProperties)
              : {}
          }
        />
      </div>
    </div>
  );
}

function TrophyIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      className="w-6 h-6 text-yellow-400"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
      />
    </svg>
  );
}
