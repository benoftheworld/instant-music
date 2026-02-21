import { useState, useEffect } from 'react';
import { gameService } from '../../services/gameService';
import type { KaraokeSong } from '../../types';

interface KaraokeSongSelectorProps {
  selectedSong: KaraokeSong | null;
  onSelectSong: (song: KaraokeSong | null) => void;
}

export default function KaraokeSongSelector({
  selectedSong,
  onSelectSong,
}: KaraokeSongSelectorProps) {
  const [songs, setSongs] = useState<KaraokeSong[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    gameService
      .listKaraokeSongs()
      .then(setSongs)
      .catch(() => setError('Impossible de charger le catalogue de morceaux.'))
      .finally(() => setLoading(false));
  }, []);

  const filtered = search.trim()
    ? songs.filter(
        (s) =>
          s.title.toLowerCase().includes(search.toLowerCase()) ||
          s.artist.toLowerCase().includes(search.toLowerCase()),
      )
    : songs;

  if (selectedSong) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-bold mb-2">🎤 Morceau sélectionné</h3>
        <div className="flex items-center gap-4 p-4 bg-pink-50 border border-pink-200 rounded-lg">
          {selectedSong.album_image_url && (
            <img
              src={selectedSong.album_image_url}
              alt={selectedSong.title}
              className="w-20 h-20 rounded-md object-cover"
            />
          )}
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-lg truncate">{selectedSong.title}</h4>
            <p className="text-sm text-gray-600 truncate">{selectedSong.artist}</p>
            <div className="flex items-center gap-3 mt-1">
              <p className="text-xs text-gray-400">
                Durée : {selectedSong.duration_display}
              </p>
              {selectedSong.lrclib_id && (
                <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
                  ✓ Paroles synchronisées
                </span>
              )}
              {!selectedSong.lrclib_id && (
                <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-medium">
                  ⚠ Paroles par recherche
                </span>
              )}
            </div>
          </div>
          <button
            onClick={() => onSelectSong(null)}
            className="text-red-600 hover:text-red-700 p-2 shrink-0"
            title="Changer de morceau"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold">🎤 Choisissez un morceau</h3>

      {/* Search input */}
      <div className="relative">
        <input
          type="text"
          placeholder="Rechercher par titre ou artiste…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input w-full pl-10"
        />
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>

      {/* States */}
      {loading && (
        <div className="text-center py-8 text-gray-500">
          <div className="inline-block w-6 h-6 border-2 border-pink-400 border-t-transparent rounded-full animate-spin mb-2" />
          <p className="text-sm">Chargement du catalogue…</p>
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="text-center py-8 text-gray-400">
          {search ? (
            <p className="text-sm">Aucun morceau ne correspond à « {search} »</p>
          ) : (
            <>
              <p className="text-4xl mb-3">🎵</p>
              <p className="text-sm font-medium">Catalogue vide</p>
              <p className="text-xs mt-1 text-gray-400">
                Les administrateurs n'ont pas encore ajouté de morceaux.
              </p>
            </>
          )}
        </div>
      )}

      {/* Song list */}
      {!loading && !error && filtered.length > 0 && (
        <ul className="space-y-2 max-h-96 overflow-y-auto pr-1">
          {filtered.map((song) => (
            <li key={song.id}>
              <button
                onClick={() => onSelectSong(song)}
                className="w-full flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-pink-300 hover:bg-pink-50 transition-all text-left"
              >
                {song.album_image_url ? (
                  <img
                    src={song.album_image_url}
                    alt={song.title}
                    className="w-14 h-14 rounded object-cover shrink-0"
                  />
                ) : (
                  <div className="w-14 h-14 rounded bg-gray-100 flex items-center justify-center text-2xl shrink-0">
                    🎵
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-semibold truncate">{song.title}</p>
                  <p className="text-sm text-gray-600 truncate">{song.artist}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-gray-400">{song.duration_display}</span>
                    {song.lrclib_id ? (
                      <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full">
                        ✓ synchronisé
                      </span>
                    ) : (
                      <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">
                        recherche auto
                      </span>
                    )}
                  </div>
                </div>
                <svg className="w-5 h-5 text-gray-300 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
