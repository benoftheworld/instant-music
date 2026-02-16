import { useState, useEffect } from 'react';
import { spotifyAuthService, SpotifyTokenInfo } from '../../services/spotifyAuthService';

export default function SpotifyConnection() {
  const [spotifyStatus, setSpotifyStatus] = useState<SpotifyTokenInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check URL parameters for OAuth callback messages
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const spotifyConnected = params.get('spotify_connected');
    const spotifyError = params.get('spotify_error');

    // If we're in a popup window (opened by window.open), close it automatically
    if (window.opener && (spotifyConnected || spotifyError)) {
      // Notify parent window to refresh
      if (window.opener && !window.opener.closed) {
        try {
          window.opener.postMessage({ 
            type: 'spotify_oauth_response', 
            success: spotifyConnected === 'true',
            error: spotifyError 
          }, window.location.origin);
        } catch (e) {
          console.error('Failed to post message to parent:', e);
        }
      }
      // Close popup
      window.close();
      return;
    }

    if (spotifyConnected === 'true') {
      // Successfully connected, refresh status
      checkStatus();
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (spotifyError) {
      // Show error message
      const errorMessages: Record<string, string> = {
        'access_denied': 'Vous avez refusé l\'accès à Spotify.',
        'invalid_callback': 'Erreur lors du callback OAuth.',
        'invalid_state': 'Erreur de sécurité (state invalide).',
        'not_authenticated': 'Vous devez être connecté.',
        'token_exchange_failed': 'Échec de l\'échange de token.',
        'user_not_found': 'Utilisateur non trouvé.'
      };
      setError(errorMessages[spotifyError] || 'Erreur de connexion Spotify.');
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // Check Spotify connection status on mount
  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      setLoading(true);
      const status = await spotifyAuthService.getStatus();
      setSpotifyStatus(status);
      setError(null);
    } catch (err: unknown) {
      console.error('Failed to check Spotify status:', err);
      setSpotifyStatus(null);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      setConnecting(true);
      setError(null);
      await spotifyAuthService.connectSpotify();
      // After user closes popup, check status
      await checkStatus();
    } catch (err: unknown) {
      console.error('Failed to connect Spotify:', err);
      setError((err as Error).message || 'Erreur lors de la connexion à Spotify.');
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Êtes-vous sûr de vouloir déconnecter votre compte Spotify ?')) {
      return;
    }

    try {
      setLoading(true);
      await spotifyAuthService.disconnect();
      setSpotifyStatus(null);
      setError(null);
    } catch (err: unknown) {
      console.error('Failed to disconnect Spotify:', err);
      setError('Erreur lors de la déconnexion.');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !connecting) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-10 bg-gray-200 rounded w-full"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <svg className="w-8 h-8 mr-3 text-green-500" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
          </svg>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Spotify</h3>
            <p className="text-sm text-gray-600">
              {spotifyStatus ? 'Compte connecté' : 'Non connecté'}
            </p>
          </div>
        </div>

        {spotifyStatus ? (
          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
              <span className="w-2 h-2 mr-2 bg-green-500 rounded-full"></span>
              Actif
            </span>
          </div>
        ) : (
          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
              <span className="w-2 h-2 mr-2 bg-gray-500 rounded-full"></span>
              Inactif
            </span>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {spotifyStatus && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-800">
            ✅ Vous avez maintenant accès à <strong>toutes les playlists Spotify</strong>, y compris vos playlists privées !
          </p>
          <p className="text-xs text-green-600 mt-2">
            Connexion: {new Date(spotifyStatus.created_at).toLocaleDateString()} • 
            Expire le: {new Date(spotifyStatus.expires_at).toLocaleDateString()}
          </p>
        </div>
      )}

      {!spotifyStatus && (
        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800 mb-2">
            <strong>Pourquoi connecter Spotify ?</strong>
          </p>
          <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
            <li>Accès à <strong>toutes les playlists publiques</strong></li>
            <li>Accès à <strong>vos playlists privées</strong></li>
            <li>Plus de problèmes 403 (Forbidden)</li>
            <li>Meilleure expérience de jeu</li>
          </ul>
        </div>
      )}

      <div className="flex gap-3">
        {spotifyStatus ? (
          <>
            <button
              onClick={handleDisconnect}
              disabled={loading}
              className="flex-1 px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Déconnexion...' : 'Déconnecter Spotify'}
            </button>
          </>
        ) : (
          <button
            onClick={handleConnect}
            disabled={connecting}
            className="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {connecting ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Connexion en cours...
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.020zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
                </svg>
                Connecter avec Spotify
              </>
            )}
          </button>
        )}
      </div>

      <p className="mt-4 text-xs text-gray-500 text-center">
        InstantMusic ne stocke que les tokens d'accès nécessaires. Vos données Spotify restent privées.
      </p>
    </div>
  );
}
