import { ReactNode } from 'react';
import { getMediaUrl } from '@/services/api';

// ── Style constants ───────────────────────────────────────────────────────────

export const DESKTOP_LINK_CLASS = 'hover:text-primary-400 transition-colors flex items-center gap-2';
export const MOBILE_LINK_CLASS = 'flex items-center gap-3 px-3 py-2.5 rounded-md hover:bg-dark-600 hover:text-primary-400 transition-colors text-sm font-medium';

// ── Icônes réutilisables ──────────────────────────────────────────────────────

export function IconLeaderboard() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M22,7H16.333V4a1,1,0,0,0-1-1H8.667a1,1,0,0,0-1,1v7H2a1,1,0,0,0-1,1v8a1,1,0,0,0,1,1H22a1,1,0,0,0,1-1V8A1,1,0,0,0,22,7ZM7.667,19H3V13H7.667Zm6.666,0H9.667V5h4.666ZM21,19H16.333V9H21Z"/>
    </svg>
  );
}

export function IconFriends() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87M16 11a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
  );
}

export function IconTeams() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v18M19 7l-7 4-7-4" />
    </svg>
  );
}

export function IconHistory() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

export function IconShop() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1.41 16.09V20h-2.67v-1.93c-1.71-.36-3.16-1.46-3.27-3.4h1.96c.1 1.05.82 1.87 2.65 1.87 1.96 0 2.4-.98 2.4-1.59 0-.83-.44-1.61-2.67-2.14-2.48-.6-4.18-1.62-4.18-3.67 0-1.72 1.39-2.84 3.11-3.21V4h2.67v1.95c1.86.45 2.79 1.86 2.85 3.39H14.3c-.05-1.11-.64-1.87-2.22-1.87-1.5 0-2.4.68-2.4 1.64 0 .84.65 1.39 2.67 1.91s4.18 1.39 4.18 3.91c-.01 1.83-1.38 2.83-3.12 3.16z"/>
    </svg>
  );
}

export function IconAdmin() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  );
}

export function IconChevron({ open }: { open: boolean }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className={`w-4 h-4 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
    </svg>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

export function getAdminHref(): string {
  const raw = (import.meta.env as any).VITE_ADMIN_URL || 'admin/';
  let href = String(raw);

  try {
    if (!href.startsWith('http')) {
      if (!href.startsWith('/')) href = `/${href}`;
      const api = (import.meta.env as any).VITE_API_URL || 'http://localhost:8000';
      try {
        const origin = new URL(api).origin;
        href = `${origin}${href}`;
      } catch (_e) {
        // fallback to root-relative
      }
    }
  } catch (_e) {
    // ignore and return raw
  }

  return href;
}

// ── Admin monitoring links ────────────────────────────────────────────────────

export const ADMIN_MONITORING_LINKS: { href: string; label: string; colorClass: string; icon: ReactNode }[] = [
  { href: '/grafana/', label: 'Grafana', colorClass: 'text-orange-400', icon: <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/> },
  { href: '/prometheus/', label: 'Prometheus', colorClass: 'text-red-400', icon: <path d="M12 2a10 10 0 100 20A10 10 0 0012 2zm0 18a8 8 0 110-16 8 8 0 010 16zm-1-5h2v2h-2zm0-8h2v6h-2z"/> },
  { href: '/kibana/', label: 'Kibana', colorClass: 'text-blue-400', icon: <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/> },
];

// ── Admin dropdown (desktop) ──────────────────────────────────────────────────

export function AdminDropdown() {
  return (
    <div className="absolute right-0 top-full mt-1 w-52 bg-dark border border-primary-500 rounded-md shadow-xl z-50 hidden group-hover:block">
      {ADMIN_MONITORING_LINKS.map(({ href, label, colorClass, icon }, i) => (
        <a
          key={href}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className={`flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-primary-600 hover:text-white transition-colors ${i === 0 ? 'rounded-t-md' : ''}`}
        >
          <svg xmlns="http://www.w3.org/2000/svg" className={`w-4 h-4 shrink-0 ${colorClass}`} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">{icon}</svg>
          {label}
        </a>
      ))}
      <div className="border-t border-primary-700 my-1" />
      <a
        href={getAdminHref()}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-primary-600 hover:text-white transition-colors rounded-b-md"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-gray-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        Admin Django
      </a>
    </div>
  );
}

// ── User avatar ───────────────────────────────────────────────────────────────

export function UserAvatar({ user, size = 'w-6 h-6' }: { user: any; size?: string }) {
  return user?.avatar ? (
    <img src={getMediaUrl(user.avatar)} alt={user.username} className={`${size} rounded-full object-cover shrink-0`} />
  ) : (
    <div className={`${size} rounded-full bg-gray-300 flex items-center justify-center text-xs text-gray-700 shrink-0`}>
      {user?.username?.charAt(0)?.toUpperCase()}
    </div>
  );
}
