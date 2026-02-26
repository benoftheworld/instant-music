import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Alpha banner */}
      <div className="bg-gradient-to-r from-amber-500 to-orange-500 text-white text-center text-xs font-bold py-1 tracking-widest uppercase select-none">
        🚧 Version Alpha — En cours de développement
      </div>
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="bg-gray-800 text-white py-4 text-center">
        <p>&copy; 2026 InstantMusic. Tous droits réservés.</p>
      </footer>
    </div>
  );
}
