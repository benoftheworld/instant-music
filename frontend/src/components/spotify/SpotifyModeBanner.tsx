import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { spotifyAuthService } from '@/services/spotifyAuthService';

export default function SpotifyModeBanner() {
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      const connected = await spotifyAuthService.isConnected();
      setIsConnected(connected);
      
      // Auto-dismiss if connected
      if (connected) {
        setDismissed(true);
      }
    } catch (error) {
      console.error('Failed to check Spotify connection:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem('spotify_banner_dismissed', 'true');
  };

  // Don't show if loading, dismissed, or already connected
  if (loading || dismissed || isConnected) {
    return null;
  }

  // Check if user previously dismissed
  if (localStorage.getItem('spotify_banner_dismissed') === 'true') {
    return null;
  }

  return (
    <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border-l-4 border-yellow-400 p-4 mb-6 rounded-lg shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="h-6 w-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div className="ml-3 flex-1">
            <h3 className="text-sm font-medium text-yellow-800">
              Accès limité aux playlists Spotify
            </h3>
            <div className="mt-2 text-sm text-yellow-700">
              <p className="mb-2">
                Vous utilisez actuellement le <strong>mode restreint</strong>. La plupart des playlists Spotify 
                publiques ne sont pas accessibles en raison des limitations de l'API.
              </p>
              <p className="mb-3">
                <strong>Solution :</strong> Connectez votre compte Spotify pour un accès complet à 
                <strong> toutes les playlists</strong>, y compris vos playlists privées !
              </p>
              <div className="flex gap-3">
                <Link
                  to="/profile"
                  className="inline-flex items-center px-4 py-2 bg-green-500 hover:bg-green-600 text-white text-sm font-medium rounded-lg transition-colors shadow-sm"
                >
                  <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.020zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
                  </svg>
                  Connecter Spotify
                </Link>
                <button
                  onClick={handleDismiss}
                  className="text-sm text-yellow-700 hover:text-yellow-900 underline"
                >
                  Ignorer
                </button>
              </div>
            </div>
          </div>
        </div>
        <button
          onClick={handleDismiss}
          className="ml-4 flex-shrink-0 text-yellow-600 hover:text-yellow-800"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
