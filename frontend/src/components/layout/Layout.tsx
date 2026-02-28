import { Outlet } from 'react-router-dom';
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
      {/* Bandeau alpha (version de développement) */}
      <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white text-center text-xs font-bold py-1 tracking-widest uppercase select-none">
        🚧 Version Alpha — En cours de développement
      </div>

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

      <footer className="bg-gray-800 text-white py-4 text-center">
        <p>&copy; 2026 InstantMusic. Tous droits réservés.</p>
      </footer>
    </div>
  );
}
