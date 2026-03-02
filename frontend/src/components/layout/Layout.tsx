import { Outlet, Link } from 'react-router-dom';
import Navbar from './Navbar';
import SiteBanner from './SiteBanner';
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
      {/* Avertissement maintenance pour les staff */}
      {maintenance && isStaff && (
        <div className="bg-primary-700 text-white text-xs font-semibold text-center py-1.5 px-4">
          ⚠️ Mode maintenance actif — vous naviguez en tant qu'administrateur
        </div>
      )}

      <Navbar />

      {/* Bannière dynamique configurée via l'admin */}
      <SiteBanner banner={banner} />

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="bg-gray-800 text-white py-5 text-center">
        <p className="text-sm">&copy; 2026 InstantMusic. Tous droits réservés.</p>
        <div className="flex justify-center gap-4 mt-2 text-xs text-gray-400">
          <Link to="/privacy" className="hover:text-white transition">
            Politique de confidentialité
          </Link>
          <span>·</span>
          <Link to="/legal" className="hover:text-white transition">
            Mentions légales
          </Link>
        </div>
      </footer>
    </div>
  );
}
