import PlaylistSelector from '../../components/playlist/PlaylistSelector';
import InviteFriendsModal from '../../components/game/InviteFriendsModal';
import LobbyHeader from './lobby/LobbyHeader';
import LobbyPlayerList from './lobby/LobbyPlayerList';
import LobbyActions from './lobby/LobbyActions';
import { useGameLobbyPage } from '../../hooks/pages/useGameLobbyPage';

export default function GameLobbyPage() {
  const {
    roomCode,
    game,
    loading,
    error,
    startError,
    startingGame,
    selectedPlaylist,
    showPlaylistSelector,
    setShowPlaylistSelector,
    copyMessage,
    showInviteModal,
    setShowInviteModal,
    isConnected,
    isHost,
    isSolo,
    handleSelectPlaylist,
    handleStartGame,
    handleLeaveGame,
    copyRoomCode,
    shareGame,
  } = useGameLobbyPage();

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-gray-600">Chargement du lobby...</p>
        </div>
      </div>
    );
  }

  if (error || !game) {
    return (
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto card">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-600 mb-4">Erreur</h1>
            <p className="text-gray-600 mb-6">{error || 'Partie introuvable'}</p>
            <button onClick={handleLeaveGame} className="btn-primary">
              Retour à l'accueil
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <LobbyHeader
          game={game}
          isConnected={isConnected}
          copyMessage={copyMessage}
          onCopyRoomCode={copyRoomCode}
          onShareGame={shareGame}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <LobbyPlayerList game={game} />

          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Mode Soirée — info block */}
            {game.is_party_mode && (
              <div className="card border-2 border-primary-200 bg-primary-50">
                <div className="flex items-start gap-3">
                  <div>
                    <h3 className="font-bold text-primary-800 mb-1">Mode Soirée activé</h3>
                    {isHost ? (
                      <p className="text-sm text-primary-700">
                        Vous êtes <strong>hôte spectateur</strong>. Projetez cet écran sur grand écran — il affichera la musique
                        et le classement. Les joueurs n'auront sur leur téléphone que les boutons de réponse.
                      </p>
                    ) : (
                      <p className="text-sm text-primary-700">
                        La musique jouera depuis l'écran projeté. Sur votre téléphone vous verrez
                        <strong> uniquement les boutons de réponse</strong>.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}
            {/* Playlist Selection — hidden for karaoke (single track pre-selected) */}
            {game.mode !== 'karaoke' && (
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold">Playlist</h2>
                {isHost && (
                  <button
                    onClick={() => setShowPlaylistSelector(!showPlaylistSelector)}
                    className="btn-secondary text-sm"
                  >
                    {showPlaylistSelector ? 'Masquer' : 'Changer'}
                  </button>
                )}
              </div>

              {selectedPlaylist || game.playlist_id ? (
                <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                  {(selectedPlaylist?.image_url || game.playlist_image_url) && (
                    <img
                      src={selectedPlaylist?.image_url || game.playlist_image_url}
                      alt={selectedPlaylist?.name || game.playlist_name || 'Playlist'}
                      className="w-20 h-20 rounded-md object-cover"
                    />
                  )}
                  <div>
                    <h3 className="font-semibold">
                      {selectedPlaylist?.name || game.playlist_name || 'Playlist sélectionnée'}
                    </h3>
                    {(selectedPlaylist || game.playlist_name) && (
                      <p className="text-sm text-gray-600">
                        {selectedPlaylist
                          ? `${selectedPlaylist.total_tracks} morceaux • ${selectedPlaylist.owner}`
                          : game.playlist_name ? `Playlist Deezer #${game.playlist_id}` : ''}
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-gray-600 text-center py-4">
                  {isHost ? 'Sélectionnez une playlist pour commencer' : 'En attente de la sélection de l\'hôte...'}
                </p>
              )}

              {showPlaylistSelector && isHost && (
                <div className="mt-4 border-t pt-4">
                  <PlaylistSelector
                    onSelectPlaylist={handleSelectPlaylist}
                    selectedPlaylistId={selectedPlaylist?.youtube_id || game.playlist_id}
                  />
                </div>
              )}
            </div>
            )}

            <LobbyActions
              game={game}
              isHost={isHost}
              isSolo={isSolo}
              startingGame={startingGame}
              startError={startError}
              onLeave={handleLeaveGame}
              onStart={handleStartGame}
              onInvite={() => setShowInviteModal(true)}
            />
          </div>
        </div>
      </div>

      {/* Invite Friends Modal */}
      {showInviteModal && roomCode && (
        <InviteFriendsModal
          roomCode={roomCode}
          onClose={() => setShowInviteModal(false)}
        />
      )}
    </div>
  );
}
