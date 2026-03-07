/**
 * InviteFriendsModal — modal permettant à l'hôte d'inviter ses amis.
 * Affiche la liste d'amis et permet d'envoyer une invitation par partie.
 */
import { useEffect, useRef, useState } from 'react';
import { friendshipService } from '@/services/socialService';
import { invitationService } from '@/services/invitationService';
import type { Friend } from '@/types';

interface Props {
  roomCode: string;
  onClose: () => void;
}

type InviteState = 'idle' | 'sending' | 'sent' | 'error';

export default function InviteFriendsModal({ roomCode, onClose }: Props) {
  const [friends, setFriends] = useState<Friend[]>([]);
  const [loadingFriends, setLoadingFriends] = useState(true);
  const [inviteStates, setInviteStates] = useState<Record<number, InviteState>>({});
  const [inviteErrors, setInviteErrors] = useState<Record<number, string>>({});
  const [searchQuery, setSearchQuery] = useState('');
  const dialogRef = useRef<HTMLDivElement>(null);

  // Focus trap + ESC handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }
      if (e.key === 'Tab' && dialogRef.current) {
        const focusable = dialogRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener('keydown', handleKeyDown);

    // Focus le champ de recherche à l'ouverture
    const searchInput = dialogRef.current?.querySelector('input');
    searchInput?.focus();

    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    friendshipService
      .getFriends()
      .then(setFriends)
      .finally(() => setLoadingFriends(false));
  }, []);

  const filteredFriends = friends.filter((f) =>
    f.user.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  async function handleInvite(friend: Friend) {
    const userId = friend.user.id;
    setInviteStates((s) => ({ ...s, [userId]: 'sending' }));
    setInviteErrors((e) => {
      const next = { ...e };
      delete next[userId];
      return next;
    });

    try {
      await invitationService.invite(roomCode, friend.user.username);
      setInviteStates((s) => ({ ...s, [userId]: 'sent' }));
    } catch (err: any) {
      const msg =
        err?.response?.data?.error || 'Erreur lors de l\'envoi de l\'invitation.';
      setInviteStates((s) => ({ ...s, [userId]: 'error' }));
      setInviteErrors((e) => ({ ...e, [userId]: msg }));
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="invite-modal-title"
        className="bg-dark border border-primary-500 rounded-xl shadow-2xl w-full max-w-md max-h-[80vh] flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-primary-700">
          <h2 id="invite-modal-title" className="text-lg font-bold text-cream-100">Inviter des amis</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-cream-100 transition-colors"
            aria-label="Fermer"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Search */}
        <div className="px-5 py-3 border-b border-primary-800">
          <input
            type="text"
            placeholder="Rechercher un ami…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-dark-600 border border-primary-700 rounded-md px-3 py-1.5 text-sm text-cream-100 placeholder-gray-500 focus:outline-none focus:border-primary-400"
          />
        </div>

        {/* Friends list */}
        <div className="flex-1 overflow-y-auto">
          {loadingFriends ? (
            <div className="flex justify-center items-center py-8">
              <div className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : filteredFriends.length === 0 ? (
            <p className="text-center text-gray-400 text-sm py-8">
              {friends.length === 0
                ? 'Vous n\'avez pas encore d\'amis.'
                : 'Aucun ami trouvé.'}
            </p>
          ) : (
            <ul className="divide-y divide-primary-800">
              {filteredFriends.map((friend) => {
                const state = inviteStates[friend.user.id] ?? 'idle';
                const errorMsg = inviteErrors[friend.user.id];
                return (
                  <li
                    key={friend.user.id}
                    className="flex items-center justify-between px-5 py-3"
                  >
                    <div>
                      <p className="text-sm font-semibold text-cream-100">
                        {friend.user.username}
                      </p>
                      {errorMsg && (
                        <p className="text-xs text-red-400 mt-0.5">{errorMsg}</p>
                      )}
                    </div>

                    {state === 'sent' ? (
                      <span className="text-xs text-green-400 font-medium flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Invité
                      </span>
                    ) : (
                      <button
                        disabled={state === 'sending'}
                        onClick={() => handleInvite(friend)}
                        className="btn py-1 px-3 text-xs bg-primary-500 text-white hover:bg-primary-600 disabled:opacity-50"
                      >
                        {state === 'sending' ? '…' : 'Inviter'}
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-primary-700">
          <p className="text-xs text-gray-500 text-center">
            Code de la partie :{' '}
            <span className="font-mono font-bold text-primary-400">{roomCode}</span>
          </p>
        </div>
      </div>
    </div>
  );
}
