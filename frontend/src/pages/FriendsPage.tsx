import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { friendshipService } from '@/services/socialService';
import { getApiErrorMessage } from '@/utils/apiError';
import { getMediaUrl } from '@/services/api';
import type { Friend, Friendship, UserMinimal } from '@/types';

export default function FriendsPage() {
  const queryClient = useQueryClient();

  const { data: friendsData, isLoading: loading } = useQuery({
    queryKey: ['friends', 'all'],
    queryFn: async () => {
      const [friendsData, pendingData, sentData] = await Promise.all([
        friendshipService.getFriends(),
        friendshipService.getPendingRequests(),
        friendshipService.getSentRequests(),
      ]);
      return {
        friends: (Array.isArray(friendsData) ? friendsData : (friendsData as any)?.results || []) as Friend[],
        pendingRequests: (Array.isArray(pendingData) ? pendingData : (pendingData as any)?.results || []) as Friendship[],
        sentRequests: (Array.isArray(sentData) ? sentData : (sentData as any)?.results || []) as Friendship[],
      };
    },
    staleTime: 30_000,
  });

  const friends = friendsData?.friends ?? [];
  const pendingRequests = friendsData?.pendingRequests ?? [];
  const sentRequests = friendsData?.sentRequests ?? [];

  const [searchResults, setSearchResults] = useState<UserMinimal[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'friends' | 'pending' | 'search'>('friends');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const invalidateFriends = () => queryClient.invalidateQueries({ queryKey: ['friends', 'all'] });

  const handleSearch = async () => {
    if (searchQuery.length < 2) return;
    try {
      const results = await friendshipService.searchUsers(searchQuery);
      setSearchResults(results);
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  const handleSendRequest = async (username: string) => {
    try {
      await friendshipService.sendRequest(username);
      setMessage({ type: 'success', text: `Demande envoyée à ${username}` });
      setSearchResults(searchResults.filter(u => u.username !== username));
      invalidateFriends();
    } catch (err: unknown) {
      setMessage({ type: 'error', text: getApiErrorMessage(err, 'Erreur') });
    }
  };

  const handleAccept = async (id: number) => {
    try {
      await friendshipService.acceptRequest(id);
      setMessage({ type: 'success', text: 'Demande acceptée !' });
      invalidateFriends();
    } catch (err) {
      setMessage({ type: 'error', text: 'Erreur lors de l\'acceptation' });
    }
  };

  const handleReject = async (id: number) => {
    try {
      await friendshipService.rejectRequest(id);
      invalidateFriends();
    } catch (err) {
      setMessage({ type: 'error', text: 'Erreur lors du refus' });
    }
  };

  const handleRemoveFriend = async (friendshipId: number) => {
    if (!window.confirm('Supprimer cet ami ?')) return;
    try {
      await friendshipService.removeFriend(friendshipId);
      invalidateFriends();
    } catch (err) {
      setMessage({ type: 'error', text: 'Erreur lors de la suppression' });
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">👥 Amis</h1>
          <p className="text-gray-600">Gérez vos amitiés et ajoutez de nouveaux amis</p>
        </div>

        {/* Message */}
        {message && (
          <div className={`mb-4 p-3 rounded-lg ${
            message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}>
            {message.text}
            <button onClick={() => setMessage(null)} className="float-right">&times;</button>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('friends')}
            className={`px-4 py-2 rounded-lg font-medium ${
              activeTab === 'friends' ? 'bg-primary-500 text-white' : 'bg-cream-200 text-dark-400 hover:bg-cream-300'
            }`}
          >
            Mes amis ({friends.length})
          </button>
          <button
            onClick={() => setActiveTab('pending')}
            className={`px-4 py-2 rounded-lg font-medium ${
              activeTab === 'pending' ? 'bg-primary-500 text-white' : 'bg-cream-200 text-dark-400 hover:bg-cream-300'
            }`}
          >
            En attente ({pendingRequests.length})
          </button>
          <button
            onClick={() => setActiveTab('search')}
            className={`px-4 py-2 rounded-lg font-medium ${
              activeTab === 'search' ? 'bg-primary-500 text-white' : 'bg-cream-200 text-dark-400 hover:bg-cream-300'
            }`}
          >
            🔍 Rechercher
          </button>
        </div>

        {/* Friends Tab */}
        {activeTab === 'friends' && (
          <div className="card">
            {loading ? (
              <div className="text-center py-8 text-gray-400">Chargement...</div>
            ) : friends.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <p>Aucun ami pour le moment</p>
                <button
                  onClick={() => setActiveTab('search')}
                  className="btn-primary mt-4"
                >
                  Ajouter des amis
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {friends.map((friend) => (
                  <div key={friend.friendship_id} className="flex items-center gap-4 p-4 bg-cream-100 rounded-lg">
                    {friend.user.avatar ? (
                      <img
                        src={getMediaUrl(friend.user.avatar)}
                        alt={friend.user.username}
                        className="w-12 h-12 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white font-bold">
                        {friend.user.username.charAt(0).toUpperCase()}
                      </div>
                    )}
                    <div className="flex-1">
                      <p className="font-bold">{friend.user.username}</p>
                      <p className="text-sm text-gray-500">{friend.user.total_points} points</p>
                    </div>
                    <button
                      onClick={() => handleRemoveFriend(friend.friendship_id)}
                      className="text-red-500 hover:text-red-700 text-sm"
                    >
                      Supprimer
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Pending Tab */}
        {activeTab === 'pending' && (
          <div className="card">
            <h3 className="font-bold mb-4">Demandes reçues</h3>
            {pendingRequests.length === 0 ? (
              <p className="text-gray-400 text-center py-4">Aucune demande en attente</p>
            ) : (
              <div className="space-y-3 mb-6">
                {pendingRequests.map((request) => (
                  <div key={request.id} className="flex items-center gap-4 p-4 bg-primary-50 rounded-lg border border-primary-200">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white font-bold">
                      {request.from_user.username.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <p className="font-bold">{request.from_user.username}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(request.created_at).toLocaleDateString('fr-FR')}
                      </p>
                    </div>
                    <button
                      onClick={() => handleAccept(request.id)}
                      className="px-3 py-1 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-500"
                    >
                      Accepter
                    </button>
                    <button
                      onClick={() => handleReject(request.id)}
                      className="px-3 py-1 bg-cream-300 text-dark-400 rounded-lg text-sm hover:bg-cream-400"
                    >
                      Refuser
                    </button>
                  </div>
                ))}
              </div>
            )}

            <h3 className="font-bold mb-4 mt-6">Demandes envoyées</h3>
            {sentRequests.length === 0 ? (
              <p className="text-gray-400 text-center py-4">Aucune demande envoyée</p>
            ) : (
              <div className="space-y-3">
                {sentRequests.map((request) => (
                  <div key={request.id} className="flex items-center gap-4 p-4 bg-cream-100 rounded-lg">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white font-bold">
                      {request.to_user.username.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <p className="font-bold">{request.to_user.username}</p>
                    </div>
                    <span className="text-sm text-dark-300">En attente...</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="card">
            <div className="flex gap-2 mb-6">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Rechercher un utilisateur..."
                className="input flex-1"
              />
              <button onClick={handleSearch} className="btn-primary">
                Rechercher
              </button>
            </div>

            {searchResults.length > 0 && (
              <div className="space-y-3">
                {searchResults.map((user) => (
                  <div key={user.id} className="flex items-center gap-4 p-4 bg-cream-100 rounded-lg">
                    {user.avatar ? (
                      <img
                        src={getMediaUrl(user.avatar)}
                        alt={user.username}
                        className="w-12 h-12 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white font-bold">
                        {user.username.charAt(0).toUpperCase()}
                      </div>
                    )}
                    <div className="flex-1">
                      <p className="font-bold">{user.username}</p>
                      <p className="text-sm text-gray-500">{user.total_points} points</p>
                    </div>
                    <button
                      onClick={() => handleSendRequest(user.username)}
                      className="btn-primary text-sm"
                    >
                      Ajouter
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
