/**
 * PlaylistSelector component
 * Search and select Deezer playlists
 */
import { useState } from 'react';
import { YouTubePlaylist } from '../../types';
import { youtubeService } from '../../services/youtubeService';
import { DEFAULT_PLAYLISTS, PLAYLIST_CATEGORIES } from '../../constants/defaultPlaylists';

interface PlaylistSelectorProps {
  onSelectPlaylist: (playlist: YouTubePlaylist) => void;
  selectedPlaylistId?: string;
}

export default function PlaylistSelector({ onSelectPlaylist, selectedPlaylistId }: PlaylistSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [playlists, setPlaylists] = useState<YouTubePlaylist[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('Tous');
  const [showSearch, setShowSearch] = useState(false);

  const popularSearches = ['Top Hits', 'Rock Classics', 'Pop Music', 'Hip Hop', 'Electronic'];

  // Convert default playlists to YouTubePlaylist format
  const getDefaultPlaylists = (): YouTubePlaylist[] => {
    return DEFAULT_PLAYLISTS.filter(
      (p) => selectedCategory === 'Tous' || p.category === selectedCategory
    ).map((p) => ({
      youtube_id: p.youtube_id,
      name: p.name,
      description: p.description,
      image_url: p.image_url,
      total_tracks: 50,
      owner: p.owner,
      external_url: `https://www.deezer.com/playlist/${p.youtube_id}`,
    }));
  };

  const defaultPlaylists = getDefaultPlaylists();

  const handleSearch = async (query?: string) => {
    const searchTerm = query || searchQuery;
    
    if (!searchTerm.trim()) {
      setError('Veuillez entrer un terme de recherche');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const results = await youtubeService.searchPlaylists(searchTerm, 20);
      setPlaylists(results);
      
      if (results.length === 0) {
        setError('Aucune playlist trouvée');
      }
    } catch (err) {
      setError('Erreur lors de la recherche des playlists');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch();
  };

  const handleSelectPlaylist = (playlist: YouTubePlaylist) => {
    onSelectPlaylist(playlist);
  };

  return (
    <div className="space-y-4">
      {/* Info Banner */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm">
        <div className="flex items-start gap-2">
          <span className="text-2xl flex-shrink-0 mt-0.5">🎵</span>
          <div>
            <p className="text-green-900 font-medium">🎶 Playlists Deezer recommandées</p>
            <p className="text-green-700 mt-1">
              Sélectionnez une playlist ci-dessous ou recherchez-en une sur Deezer.
            </p>
          </div>
        </div>
      </div>

      {/* Category Filter */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-gray-900">Playlists recommandées</h3>
          <button
            onClick={() => setShowSearch(!showSearch)}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            {showSearch ? '← Retour aux recommandations' : 'Rechercher une playlist →'}
          </button>
        </div>
        
        {!showSearch && (
          <div className="flex flex-wrap gap-2">
            {PLAYLIST_CATEGORIES.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  selectedCategory === category
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Search Section (collapsible) */}
      {showSearch && (
        <div className="space-y-3 border-t pt-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Rechercher une playlist Deezer..."
              className="input flex-1"
            />
            <button
              type="submit"
              disabled={loading}
              className="btn-primary"
            >
              {loading ? 'Recherche...' : 'Rechercher'}
            </button>
          </form>

          {/* Popular Searches */}
          <div className="flex flex-wrap gap-2">
            <span className="text-sm text-gray-600">Populaires :</span>
            {popularSearches.map((search) => (
              <button
                key={search}
                onClick={() => {
                  setSearchQuery(search);
                  handleSearch(search);
                }}
                className="text-sm px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
              >
                {search}
              </button>
            ))}
          </div>

          {/* Info for search */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
            💡 Recherchez des playlists Deezer publiques. Les playlists privées ne sont pas accessibles.
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p className="mt-2 text-gray-600">Recherche en cours...</p>
        </div>
      )}

      {/* Playlist Grid */}
      {!loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {(showSearch ? playlists : defaultPlaylists).map((playlist) => (
            <button
              key={playlist.youtube_id}
              onClick={() => onSelectPlaylist(playlist)}
              className={`
                card p-4 text-left transition-all hover:shadow-lg hover:scale-105
                ${selectedPlaylistId === playlist.youtube_id 
                  ? 'ring-2 ring-primary-600 bg-primary-50' 
                  : 'hover:bg-gray-50'
                }
              `}
            >
              {/* Playlist Image */}
              <div className="relative pb-[100%] mb-3 overflow-hidden rounded-md bg-gray-200">
                {playlist.image_url ? (
                  <img
                    src={playlist.image_url}
                    alt={playlist.name}
                    className="absolute inset-0 w-full h-full object-cover"
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <svg className="w-12 h-12 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z" />
                    </svg>
                  </div>
                )}
                
                {/* Selection Indicator */}
                {selectedPlaylistId === playlist.youtube_id && (
                  <div className="absolute top-2 right-2 bg-primary-600 text-white rounded-full p-1">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>

              {/* Playlist Info */}
              <h3 className="font-semibold text-sm mb-1 line-clamp-2">
                {playlist.name}
              </h3>
              <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                {playlist.description || 'Pas de description'}
              </p>
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>{playlist.total_tracks || '~50'} morceaux</span>
                <span className="truncate ml-2">{playlist.owner}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Empty State for defaults */}
      {!loading && !showSearch && defaultPlaylists.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          Aucune playlist dans cette catégorie
        </div>
      )}

      {/* Empty State for search */}
      {!loading && showSearch && playlists.length === 0 && !error && (
        <div className="text-center py-8 text-gray-500">
          Recherchez une playlist ou retournez aux recommandations
        </div>
      )}
    </div>
  );
}
