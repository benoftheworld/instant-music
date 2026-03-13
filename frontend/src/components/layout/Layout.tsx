import { Outlet, Link } from 'react-router-dom';
import Navbar from './Navbar';
import SiteBanner from './SiteBanner';
import ConsentBanner from './ConsentBanner';
import MaintenancePage from './MaintenancePage';
import { useSiteStatus } from '@/hooks/useSiteStatus';
import { useAuthStore } from '@/store/authStore';

export default function Layout() {
  const { maintenance, maintenance_title, maintenance_message, banner } = useSiteStatus();
  const user = useAuthStore((s) => s.user);
  const isStaff = user?.is_staff ?? false;

  // Mode maintenance actif : les non-staff voient la page de maintenance
  if (maintenance && !isStaff) {
    return <MaintenancePage title={maintenance_title} message={maintenance_message} />;
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Skip link — accessibilité */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[100] focus:bg-primary-600 focus:text-white focus:px-4 focus:py-2 focus:rounded focus:text-sm focus:font-semibold"
      >
        Passer au contenu
      </a>

      {/* Avertissement maintenance pour les staff */}
      {maintenance && isStaff && (
        <div className="bg-primary-700 text-white text-xs font-semibold text-center py-1.5 px-4">
          ⚠️ Mode maintenance actif — vous naviguez en tant qu'administrateur
        </div>
      )}

      <Navbar />

      {/* Bannière dynamique configurée via l'admin */}
      <SiteBanner banner={banner} />

      <main id="main-content" className="flex-1">
        <Outlet />
      </main>

      <footer className="bg-dark text-cream-100 py-5 text-center">
        <p className="text-sm">&copy; 2026 InstantMusic. Tous droits réservés.</p>
        <div className="flex justify-center gap-4 mt-2 text-xs text-cream-300">
          <Link to="/privacy" className="hover:text-white transition">
            Politique de confidentialité
          </Link>
          <span>·</span>
          <Link to="/legal" className="hover:text-white transition">
            Mentions légales
          </Link>
        </div>
      </footer>

      <ConsentBanner />
    </div>
  );
}
