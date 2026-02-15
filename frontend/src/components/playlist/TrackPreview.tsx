/**
 * TrackPreview component
 * Display and play track preview (30 seconds)
 */
import { useState, useRef, useEffect } from 'react';
import { SpotifyTrack } from '../../types';
import { spotifyService } from '../../services/spotifyService';

interface TrackPreviewProps {
  track: SpotifyTrack;
  autoPlay?: boolean;
  showControls?: boolean;
}

export default function TrackPreview({ track, autoPlay = false, showControls = true }: TrackPreviewProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (autoPlay && track.preview_url && audioRef.current) {
      audioRef.current.play().catch(console.error);
      setIsPlaying(true);
    }

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, [track.spotify_id, autoPlay]);

  const togglePlay = () => {
    if (!audioRef.current || !track.preview_url) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch(console.error);
    }
    setIsPlaying(!isPlaying);
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleEnded = () => {
    setIsPlaying(false);
    setCurrentTime(0);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex items-center gap-4 p-4 bg-white rounded-lg shadow-sm">
      {/* Album Art */}
      <div className="flex-shrink-0">
        {track.album_image ? (
          <img
            src={track.album_image}
            alt={track.album}
            className="w-16 h-16 rounded-md object-cover"
          />
        ) : (
          <div className="w-16 h-16 rounded-md bg-gray-200 flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path d="M18 3a1 1 0 00-1.196-.98l-10 2A1 1 0 006 5v9.114A4.369 4.369 0 005 14c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V7.82l8-1.6v5.894A4.37 4.37 0 0015 12c-1.657 0-3 .895-3 2s1.343 2 3 2 3-.895 3-2V3z" />
            </svg>
          </div>
        )}
      </div>

      {/* Track Info & Controls */}
      <div className="flex-1 min-w-0">
        <h4 className="font-semibold text-sm truncate">{track.name}</h4>
        <p className="text-xs text-gray-600 truncate">
          {track.artists.join(', ')} • {track.album}
        </p>

        {/* Audio Controls */}
        {showControls && track.preview_url ? (
          <div className="mt-2 flex items-center gap-3">
            <button
              onClick={togglePlay}
              className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-primary-600 hover:bg-primary-700 text-white rounded-full transition-colors"
            >
              {isPlaying ? (
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                </svg>
              )}
            </button>

            {/* Progress Bar */}
            <div className="flex-1 flex items-center gap-2">
              <span className="text-xs text-gray-500 w-10 text-right">
                {formatTime(currentTime)}
              </span>
              <input
                type="range"
                min="0"
                max={duration || 30}
                step="0.1"
                value={currentTime}
                onChange={handleSeek}
                className="flex-1 h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, #2563eb ${(currentTime / (duration || 30)) * 100}%, #e5e7eb ${(currentTime / (duration || 30)) * 100}%)`
                }}
              />
              <span className="text-xs text-gray-500 w-10">
                {formatTime(duration || 30)}
              </span>
            </div>
          </div>
        ) : !track.preview_url ? (
          <p className="text-xs text-gray-500 mt-2">Aperçu non disponible</p>
        ) : null}

        {/* Hidden Audio Element */}
        {track.preview_url && (
          <audio
            ref={audioRef}
            src={track.preview_url}
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onEnded={handleEnded}
          />
        )}
      </div>

      {/* Duration Badge */}
      <div className="flex-shrink-0 text-xs text-gray-500">
        {spotifyService.formatDuration(track.duration_ms)}
      </div>
    </div>
  );
}
