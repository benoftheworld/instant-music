import { useState, useEffect } from 'react';
import type { SiteBannerData } from '@/services/adminService';

interface Props {
  banner: SiteBannerData;
}

const DISMISSED_KEY = 'site_banner_dismissed';

const COLOR_CLASSES: Record<SiteBannerData['color'], string> = {
  info: 'bg-blue-600 text-white',
  success: 'bg-green-600 text-white',
  warning: 'bg-amber-500 text-white',
  danger: 'bg-primary-600 text-white',
};

export default function SiteBanner({ banner }: Props) {
  const [dismissed, setDismissed] = useState(false);

  // Réinitialiser si le message change
  useEffect(() => {
    const key = `${DISMISSED_KEY}_${banner.message}`;
    setDismissed(sessionStorage.getItem(key) === '1');
  }, [banner.message]);

  if (!banner.enabled || dismissed) return null;

  const handleDismiss = () => {
    const key = `${DISMISSED_KEY}_${banner.message}`;
    sessionStorage.setItem(key, '1');
    setDismissed(true);
  };

  return (
    <div className={`${COLOR_CLASSES[banner.color]} px-4 py-2 text-sm font-medium`}>
      <div className="container mx-auto flex items-center justify-between gap-4">
        <p className="flex-1 text-center">{banner.message}</p>
        {banner.dismissible && (
          <button
            onClick={handleDismiss}
            aria-label="Fermer le bandeau"
            className="shrink-0 rounded hover:opacity-75 transition-opacity p-0.5"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
