import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { friendshipService } from '@/services/socialService';
import { getApiErrorMessage } from '@/utils/apiError';
import { QUERY_KEYS } from '@/constants/queryKeys';
import type { Friend, Friendship, UserMinimal } from '@/types';

export function useFriendsPage() {
  const queryClient = useQueryClient();

  const { data: friendsData, isLoading: loading } = useQuery({
    queryKey: QUERY_KEYS.friends(),
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

  const invalidateFriends = () => queryClient.invalidateQueries({ queryKey: QUERY_KEYS.friends() });

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
      setMessage({ 
        type: 'error', 
        text: 'Erreur lors de l\'acceptation de la demande' + 
          (getApiErrorMessage(err, '') ? ': ' + getApiErrorMessage(err, '') : '') }
      );
    }
  };

  const handleReject = async (id: number) => {
    try {
      await friendshipService.rejectRequest(id);
      invalidateFriends();
    } catch (err) {
      setMessage({ type: 'error', text: 'Erreur lors du refus' + (getApiErrorMessage(err, '') ? ': ' + getApiErrorMessage(err, '') : '') });
    }
  };

  const handleRemoveFriend = async (friendshipId: number) => {
    if (!window.confirm('Supprimer cet ami ?')) return;
    try {
      await friendshipService.removeFriend(friendshipId);
      invalidateFriends();
    } catch (err) {
      setMessage({ type: 'error', text: 'Erreur lors de la suppression' + (getApiErrorMessage(err, '') ? ': ' + getApiErrorMessage(err, '') : '') });
    }
  };

  return {
    loading,
    friends,
    pendingRequests,
    sentRequests,
    searchResults,
    searchQuery,
    setSearchQuery,
    activeTab,
    setActiveTab,
    message,
    setMessage,
    handleSearch,
    handleSendRequest,
    handleAccept,
    handleReject,
    handleRemoveFriend,
  };
}
