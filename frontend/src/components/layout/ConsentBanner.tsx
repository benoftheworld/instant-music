import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const CONSENT_KEY = 'rgpd_consent';

export default function ConsentBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem(CONSENT_KEY)) {
      setVisible(true);
    }
  }, []);

  if (!visible) return null;

  const accept = () => {
    localStorage.setItem(CONSENT_KEY, new Date().toISOString());
    setVisible(false);
  };

  return (
    <div className="fixed bottom-0 inset-x-0 z-50 bg-gray-900/95 backdrop-blur text-white px-4 py-4 shadow-lg">
      <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center gap-3 text-sm">
        <p className="flex-1 text-center sm:text-left">
          Ce site utilise des données locales pour fonctionner. En continuant, vous acceptez
          notre{' '}
          <Link to="/privacy" className="underline hover:text-primary-300">
            politique de confidentialité
          </Link>
          .
        </p>
        <div className="flex gap-2 shrink-0">
          <Link
            to="/privacy"
            className="px-3 py-1.5 text-xs border border-gray-500 rounded hover:bg-gray-700 transition"
          >
            En savoir plus
          </Link>
          <button
            onClick={accept}
            className="px-4 py-1.5 text-xs font-semibold bg-primary-600 rounded hover:bg-primary-500 transition"
          >
            J&apos;accepte
          </button>
        </div>
      </div>
    </div>
  );
}
