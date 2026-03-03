/**
 * NotificationBell — icône dans la navbar affichant les invitations en attente.
 * Un clic ouvre un dropdown listant les invitations avec boutons Accepter/Refuser.
 */
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useNotificationStore } from '@/store/notificationStore';
import { invitationService } from '@/services/invitationService';
import type { GameInvitation } from '@/types';

const MODE_LABELS: Record<string, string> = {
  classique: 'Classique',
  rapide: 'Rapide',
  generation: 'Génération',
  paroles: 'Paroles',
  karaoke: 'Karaoké',
};

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const { invitations, removeInvitation } = useNotificationStore();
  const count = invitations.length;

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  async function handleAccept(invitation: GameInvitation) {
    setLoading(invitation.id);
    try {
      const { room_code } = await invitationService.accept(invitation.id);
      removeInvitation(invitation.id);
      setOpen(false);
      navigate(`/game/lobby/${room_code}`);
    } catch (err: any) {
      const msg = err?.response?.data?.error || 'Erreur lors de l\'acceptation.';
      alert(msg);
    } finally {
      setLoading(null);
    }
  }

  async function handleDecline(invitation: GameInvitation) {
    setLoading(invitation.id);
    try {
      await invitationService.decline(invitation.id);
      removeInvitation(invitation.id);
    } catch {
      removeInvitation(invitation.id);
    } finally {
      setLoading(null);
    }
  }

  if (count === 0 && !open) {
    // Show ghost bell when no invitations
    return (
      <button
        aria-label="Notifications"
        className="relative p-1 text-cream-100 hover:text-primary-400 transition-colors"
        onClick={() => setOpen(true)}
      >
        <BellIcon />
      </button>
    );
  }

  return (
    <div ref={dropdownRef} className="relative">
      <button
        aria-label={`${count} invitation${count > 1 ? 's' : ''} en attente`}
        className="relative p-1 text-cream-100 hover:text-primary-400 transition-colors"
        onClick={() => setOpen((o) => !o)}
      >
        <BellIcon />
        {count > 0 && (
          <span className="absolute -top-1 -right-1 flex items-center justify-center w-4 h-4 rounded-full bg-red-500 text-white text-[10px] font-bold leading-none">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-dark border border-primary-500 rounded-lg shadow-2xl z-50">
          <div className="px-4 py-2.5 border-b border-primary-700">
            <p className="text-sm font-semibold text-cream-100">
              Invitations de partie{count > 0 ? ` (${count})` : ''}
            </p>
          </div>

          {count === 0 ? (
            <p className="px-4 py-4 text-sm text-gray-400 text-center">
              Aucune invitation en attente
            </p>
          ) : (
            <ul className="max-h-96 overflow-y-auto divide-y divide-primary-800">
              {invitations.map((inv) => (
                <li key={inv.id} className="px-4 py-3">
                  <p className="text-sm text-cream-100 mb-1">
                    <span className="font-semibold text-primary-400">
                      {inv.sender.username}
                    </span>{' '}
                    vous invite à une partie{' '}
                    <span className="font-semibold">
                      {MODE_LABELS[inv.game_mode] ?? inv.game_mode}
                    </span>
                    {inv.game_name ? ` « ${inv.game_name} »` : ''}
                  </p>
                  <p className="text-xs text-gray-400 mb-2">
                    Code : <span className="font-mono font-bold">{inv.room_code}</span>
                  </p>
                  <div className="flex gap-2">
                    <button
                      disabled={loading === inv.id}
                      onClick={() => handleAccept(inv)}
                      className="flex-1 btn py-1 text-xs bg-primary-500 text-white hover:bg-primary-600 disabled:opacity-50"
                    >
                      {loading === inv.id ? '…' : 'Rejoindre'}
                    </button>
                    <button
                      disabled={loading === inv.id}
                      onClick={() => handleDecline(inv)}
                      className="flex-1 btn py-1 text-xs bg-transparent border border-gray-500 text-gray-300 hover:border-red-400 hover:text-red-400 disabled:opacity-50"
                    >
                      Refuser
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function BellIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      className="w-5 h-5"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
      />
    </svg>
  );
}
