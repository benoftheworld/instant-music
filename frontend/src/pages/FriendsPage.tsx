import { Avatar, Alert, Button, EmptyState, LoadingState } from '@/components/ui';
import { useFriendsPage } from '@/hooks/pages/useFriendsPage';

export default function FriendsPage() {
  const {
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
  } = useFriendsPage();

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
          <Alert
            variant={message.type}
            onClose={() => setMessage(null)}
            className="mb-4"
          >
            {message.text}
          </Alert>
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
              <LoadingState message="Chargement..." />
            ) : friends.length === 0 ? (
              <EmptyState
                title="Aucun ami pour le moment"
                action={
                  <Button onClick={() => setActiveTab('search')}>Ajouter des amis</Button>
                }
              />
            ) : (
              <div className="space-y-3">
                {friends.map((friend) => (
                  <div key={friend.friendship_id} className="flex items-center gap-4 p-4 bg-cream-100 rounded-lg">
                    <Avatar src={friend.user.avatar} username={friend.user.username} size="lg" />
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
                    <Avatar src={null} username={request.from_user.username} />
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
                    <Avatar src={null} username={request.to_user.username} />
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
                    <Avatar src={user.avatar} username={user.username} size="lg" />
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
