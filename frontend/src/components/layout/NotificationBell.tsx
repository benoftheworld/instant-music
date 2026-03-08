/**
 * NotificationBell — icône dans la navbar affichant toutes les notifications en attente.
 * Invitations de partie, demandes d'ami, notifications sociales.
 */
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useNotificationStore } from '@/store/notificationStore';
import { invitationService } from '@/services/invitationService';
import { friendshipService } from '@/services/socialService';
import { getModeLabel } from '@/constants/gameModes';
import type { GameInvitation } from '@/types';
import type { PendingFriendRequest, SocialNotification } from '@/store/notificationStore';

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const {
    invitations,
    friendRequests,
    socialNotifications,
    removeInvitation,
    removeFriendRequest,
    removeSocialNotification,
  } = useNotificationStore();

  const count = invitations.length + friendRequests.length + socialNotifications.length;

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  async function handleAcceptInvitation(invitation: GameInvitation) {
    setLoading(`inv-${invitation.id}`);
    try {
      const { room_code } = await invitationService.accept(invitation.id);
      removeInvitation(invitation.id);
      setOpen(false);
      navigate(`/game/lobby/${room_code}`);
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Erreur lors de l\'acceptation.');
    } finally {
      setLoading(null);
    }
  }

  async function handleDeclineInvitation(invitation: GameInvitation) {
    setLoading(`inv-${invitation.id}`);
    try {
      await invitationService.decline(invitation.id);
    } catch {
      // ignore
    } finally {
      removeInvitation(invitation.id);
      setLoading(null);
    }
  }

  async function handleAcceptFriend(req: PendingFriendRequest) {
    setLoading(`fr-${req.id}`);
    try {
      await friendshipService.acceptRequest(req.id);
      removeFriendRequest(req.id);
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Erreur lors de l\'acceptation.');
    } finally {
      setLoading(null);
    }
  }

  async function handleDeclineFriend(req: PendingFriendRequest) {
    setLoading(`fr-${req.id}`);
    try {
      await friendshipService.rejectRequest(req.id);
    } catch {
      // ignore
    } finally {
      removeFriendRequest(req.id);
      setLoading(null);
    }
  }

  function handleSocialClick(notif: SocialNotification) {
    removeSocialNotification(notif.id);
    if (notif.link) {
      navigate(notif.link);
      setOpen(false);
    }
  }

  if (count === 0 && !open) {
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
        aria-label={`${count} notification${count > 1 ? 's' : ''} en attente`}
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
              Notifications{count > 0 ? ` (${count})` : ''}
            </p>
          </div>

          {count === 0 ? (
            <p className="px-4 py-4 text-sm text-gray-400 text-center">
              Aucune notification en attente
            </p>
          ) : (
            <ul className="max-h-96 overflow-y-auto divide-y divide-primary-800">

              {/* ── Invitations de partie ── */}
              {invitations.map((inv) => (
                <li key={`inv-${inv.id}`} className="px-4 py-3">
                  <p className="text-xs text-primary-400 font-semibold uppercase tracking-wide mb-1">
                    Invitation de partie
                  </p>
                  <p className="text-sm text-cream-100 mb-1">
                    <span className="font-semibold">{inv.sender.username}</span>{' '}
                    vous invite à{' '}
                    <span className="font-semibold">{getModeLabel(inv.game_mode)}</span>
                    {inv.game_name ? ` « ${inv.game_name} »` : ''}
                  </p>
                  <p className="text-xs text-gray-400 mb-2">
                    Code : <span className="font-mono font-bold">{inv.room_code}</span>
                  </p>
                  <div className="flex gap-2">
                    <button
                      disabled={loading === `inv-${inv.id}`}
                      onClick={() => handleAcceptInvitation(inv)}
                      className="flex-1 btn py-1 text-xs bg-primary-500 text-white hover:bg-primary-600 disabled:opacity-50"
                    >
                      {loading === `inv-${inv.id}` ? '…' : 'Rejoindre'}
                    </button>
                    <button
                      disabled={loading === `inv-${inv.id}`}
                      onClick={() => handleDeclineInvitation(inv)}
                      className="flex-1 btn py-1 text-xs bg-transparent border border-gray-500 text-gray-300 hover:border-red-400 hover:text-red-400 disabled:opacity-50"
                    >
                      Refuser
                    </button>
                  </div>
                </li>
              ))}

              {/* ── Demandes d'ami ── */}
              {friendRequests.map((req) => (
                <li key={`fr-${req.id}`} className="px-4 py-3">
                  <p className="text-xs text-blue-400 font-semibold uppercase tracking-wide mb-1">
                    Demande d'ami
                  </p>
                  <p className="text-sm text-cream-100 mb-2">
                    <span className="font-semibold">{req.from_user.username}</span>{' '}
                    vous a envoyé une demande d'ami.
                  </p>
                  <div className="flex gap-2">
                    <button
                      disabled={loading === `fr-${req.id}`}
                      onClick={() => handleAcceptFriend(req)}
                      className="flex-1 btn py-1 text-xs bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50"
                    >
                      {loading === `fr-${req.id}` ? '…' : 'Accepter'}
                    </button>
                    <button
                      disabled={loading === `fr-${req.id}`}
                      onClick={() => handleDeclineFriend(req)}
                      className="flex-1 btn py-1 text-xs bg-transparent border border-gray-500 text-gray-300 hover:border-red-400 hover:text-red-400 disabled:opacity-50"
                    >
                      Refuser
                    </button>
                  </div>
                </li>
              ))}

              {/* ── Notifications sociales ── */}
              {socialNotifications.map((notif) => (
                <li key={notif.id} className="px-4 py-3 flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold uppercase tracking-wide mb-0.5 text-green-400">
                      {notif.type === 'friend_request_accepted' && 'Ami'}
                      {notif.type === 'team_join_request' && 'Équipe'}
                      {notif.type === 'team_join_approved' && 'Équipe'}
                    </p>
                    <p className="text-sm text-cream-100 leading-snug">{notif.message}</p>
                    {notif.link && (
                      <button
                        onClick={() => handleSocialClick(notif)}
                        className="text-xs text-primary-400 hover:underline mt-1"
                      >
                        Voir →
                      </button>
                    )}
                  </div>
                  <button
                    onClick={() => removeSocialNotification(notif.id)}
                    className="text-gray-500 hover:text-gray-300 flex-shrink-0 mt-0.5"
                    aria-label="Fermer"
                  >
                    <XIcon />
                  </button>
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

function XIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}
