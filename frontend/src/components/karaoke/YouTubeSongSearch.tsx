import { useState, useCallback, useRef } from 'react';
import { youtubeService } from '../../services/youtubeService';
import type { YouTubeTrack, KaraokeTrack } from '../../types';

interface YouTubeSongSearchProps {
  selectedTrack: KaraokeTrack | null;
  onSelectTrack: (track: KaraokeTrack | null) => void;
}

export default function YouTubeSongSearch({
  selectedTrack,
  onSelectTrack,
}: YouTubeSongSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<YouTubeTrack[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const doSearch = useCallback(async (searchQuery: string) => {
    if (searchQuery.trim().length < 2) {
      setResults([]);
      setSearched(false);
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const tracks = await youtubeService.searchYouTubeSongs(searchQuery.trim(), 8);
      setResults(tracks);
    } catch {
      setError('Erreur lors de la recherche YouTube. Réessayez.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleInputChange = (value: string) => {
    setQuery(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(value), 500);
  };

  const handleSelect = (track: YouTubeTrack) => {
    const karaokeTrack: KaraokeTrack = {
      youtube_video_id: track.youtube_id,
      track_name: track.name,
      artist_name: track.artists.join(', '),
      duration_ms: track.duration_ms,
      album_image: track.album_image,
    };
    onSelectTrack(karaokeTrack);
  };

  const formatDuration = (ms: number): string => {
    if (!ms) return '--:--';
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // If a track is selected, show it with a remove button
  if (selectedTrack) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-bold mb-2">🎤 Morceau sélectionné</h3>
        <div className="flex items-center gap-4 p-4 bg-pink-50 border border-pink-200 rounded-lg">
          {selectedTrack.album_image && (
            <img
              src={selectedTrack.album_image}
              alt={selectedTrack.track_name}
              className="w-20 h-20 rounded-md object-cover"
            />
          )}
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-lg truncate">{selectedTrack.track_name}</h4>
            <p className="text-sm text-gray-600 truncate">{selectedTrack.artist_name}</p>
            <p className="text-xs text-gray-400 mt-1">
              Durée : {formatDuration(selectedTrack.duration_ms)}
            </p>
          </div>
          <button
            onClick={() => onSelectTrack(null)}
            className="text-red-600 hover:text-red-700 p-2 shrink-0"
            title="Retirer"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold mb-2">🔍 Rechercher un morceau YouTube</h3>

      {/* Search input */}
      <div className="relative">
        <input
          type="text"
          placeholder="Ex: Bohemian Rhapsody, Stromae Papaoutai..."
          value={query}
          onChange={(e) => handleInputChange(e.target.value)}
          className="input w-full pl-10"
        />
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600" />
          </div>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {results.map((track) => (
            <button
              key={track.youtube_id}
              onClick={() => handleSelect(track)}
              className="w-full flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-pink-400 hover:bg-pink-50 transition-all text-left"
            >
              {track.album_image && (
                <img
                  src={track.album_image}
                  alt={track.name}
                  className="w-12 h-12 rounded object-cover shrink-0"
                />
              )}
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate">{track.name}</p>
                <p className="text-xs text-gray-500 truncate">
                  {track.artists.join(', ')}
                </p>
              </div>
              <span className="text-xs text-gray-400 shrink-0">
                {formatDuration(track.duration_ms)}
              </span>
            </button>
          ))}
        </div>
      )}

      {searched && !loading && results.length === 0 && !error && (
        <div className="text-center py-6 text-gray-500">
          <p className="text-sm">Aucun résultat trouvé pour « {query} »</p>
          <p className="text-xs mt-1">Essayez avec d'autres mots-clés</p>
        </div>
      )}

      {!searched && (
        <div className="text-center py-6">
          <svg
            className="w-12 h-12 text-gray-400 mx-auto mb-3"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z" />
          </svg>
          <p className="text-gray-600 text-sm">
            Recherchez un morceau pour lancer le karaoké
          </p>
        </div>
      )}
    </div>
  );
}
