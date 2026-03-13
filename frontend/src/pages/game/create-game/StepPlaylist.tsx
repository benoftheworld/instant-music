import PlaylistSelector from '../../../components/playlist/PlaylistSelector';
import KaraokeSongSelector from '../../../components/karaoke/KaraokeSongSelector';
import type { YouTubePlaylist, KaraokeSong } from '../../../types';

interface Props {
  isKaraoke: boolean;
  selectedPlaylist: YouTubePlaylist | null;
  karaokeSelectedSong: KaraokeSong | null;
  onSelectPlaylist: (p: YouTubePlaylist | null) => void;
  onSelectKaraokeSong: (s: KaraokeSong | null) => void;
}

export default function StepPlaylist({
  isKaraoke,
  selectedPlaylist,
  karaokeSelectedSong,
  onSelectPlaylist,
  onSelectKaraokeSong,
}: Props) {
  return (
    <div className="card">
      {isKaraoke ? (
        <KaraokeSongSelector
          selectedSong={karaokeSelectedSong}
          onSelectSong={onSelectKaraokeSong}
        />
      ) : (
        <>
          {selectedPlaylist ? (
            <div className="mb-6">
              <div className="flex items-center gap-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                {selectedPlaylist.image_url && (
                  <img
                    src={selectedPlaylist.image_url}
                    alt={selectedPlaylist.name}
                    className="w-20 h-20 rounded-md object-cover"
                  />
                )}
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{selectedPlaylist.name}</h3>
                  <p className="text-sm text-gray-600">
                    {selectedPlaylist.total_tracks} morceaux • {selectedPlaylist.owner}
                  </p>
                </div>
                <button
                  onClick={() => onSelectPlaylist(null)}
                  className="text-red-600 hover:text-red-700 p-2"
                  title="Retirer"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-4 mb-4">
              <svg className="w-12 h-12 text-gray-400 mx-auto mb-3" fill="currentColor" viewBox="0 0 20 20">
                <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z" />
              </svg>
              <p className="text-gray-600">Sélectionnez une playlist ci-dessous</p>
            </div>
          )}

          <PlaylistSelector
            onSelectPlaylist={onSelectPlaylist}
            selectedPlaylistId={selectedPlaylist?.youtube_id}
          />
        </>
      )}
    </div>
  );
}
