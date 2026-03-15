import { useState, useEffect, useRef } from 'react';
import { soundEffects } from '../../services/soundEffects';

const STORAGE_KEY_VOLUME = 'im_volume';
const STORAGE_KEY_MUTED = 'im_muted';
const STORAGE_KEY_MUSIC_VOLUME = 'im_music_volume';

/**
 * Read persisted volume settings from localStorage and apply them.
 * Call this once on app startup (e.g. in App.tsx or main.tsx).
 */
export function initVolumeSettings() {
  try {
    const muted = localStorage.getItem(STORAGE_KEY_MUTED);
    if (muted !== null) {
      soundEffects.setEnabled(muted !== 'true');
      _musicMuted = muted === 'true';
    }
    const vol = localStorage.getItem(STORAGE_KEY_VOLUME);
    if (vol !== null) {
      soundEffects.setVolume(parseFloat(vol));
    }
    const musicVol = localStorage.getItem(STORAGE_KEY_MUSIC_VOLUME);
    if (musicVol !== null) {
      setGlobalMusicVolume(parseFloat(musicVol));
    }
  } catch {
    // Ignore localStorage errors
  }
}

/* ───────────────────── Global music volume ───────────────────── */
let _musicVolume = 1.0;
let _musicMuted = false;

/** Volume du slider (valeur brute, indépendante du mute). */
export function getGlobalMusicVolume(): number {
  return _musicVolume;
}

export function setGlobalMusicVolume(v: number) {
  _musicVolume = Math.max(0, Math.min(1, v));
}

/** Volume effectif appliqué aux éléments audio (0 si muted). */
export function getEffectiveMusicVolume(): number {
  return _musicMuted ? 0 : _musicVolume;
}

/** Met à jour l'état mute musique et notifie les éléments audio existants. */
export function setGlobalMusicMuted(m: boolean) {
  _musicMuted = m;
  window.dispatchEvent(new CustomEvent('music-volume-change'));
}

/* ───────────────────── VolumeControl component ───────────────────── */

interface VolumeControlProps {
  /** Render as a compact floating button (for in-game) or a full settings card */
  variant?: 'floating' | 'card';
}

export default function VolumeControl({ variant = 'floating' }: VolumeControlProps) {
  const [muted, setMuted] = useState(!soundEffects.isEnabled());
  const [effectsVolume, setEffectsVolume] = useState(soundEffects.getVolume());
  const [musicVolume, setMusicVolume] = useState(getGlobalMusicVolume());
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close popup on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const persist = (m: boolean, ev: number, mv: number) => {
    try {
      localStorage.setItem(STORAGE_KEY_MUTED, String(m));
      localStorage.setItem(STORAGE_KEY_VOLUME, String(ev));
      localStorage.setItem(STORAGE_KEY_MUSIC_VOLUME, String(mv));
    } catch { /* */ }
  };

  const handleMuteToggle = () => {
    const next = !muted;
    setMuted(next);
    soundEffects.setEnabled(!next);
    setGlobalMusicMuted(next);
    persist(next, effectsVolume, musicVolume);
  };

  const handleEffectsVolumeChange = (v: number) => {
    setEffectsVolume(v);
    soundEffects.setVolume(v);
    persist(muted, v, musicVolume);
  };

  const handleMusicVolumeChange = (v: number) => {
    setMusicVolume(v);
    setGlobalMusicVolume(v);
    persist(muted, effectsVolume, v);
    window.dispatchEvent(new CustomEvent('music-volume-change', { detail: v }));
  };

  const icon = muted ? '🔇' : effectsVolume > 0.5 ? '🔊' : effectsVolume > 0 ? '🔉' : '🔈';

  if (variant === 'card') {
    return (
      <div className="card">
        <h2 className="text-2xl font-bold mb-4 flex items-center">
          Réglages du son
        </h2>

        <div className="space-y-5">
          {/* Mute toggle */}
          <div className="flex items-center justify-between">
            <span className="font-medium text-gray-700">Son activé</span>
            <button
              onClick={handleMuteToggle}
              className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors ${
                !muted ? 'bg-primary-500' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                  !muted ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Effects volume */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm font-medium text-gray-700">Effets sonores</label>
              <span className="text-sm text-gray-500">{Math.round(effectsVolume * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={effectsVolume}
              onChange={(e) => handleEffectsVolumeChange(parseFloat(e.target.value))}
              disabled={muted}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-500 disabled:opacity-50"
            />
          </div>

          {/* Music volume */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm font-medium text-gray-700">Volume musique</label>
              <span className="text-sm text-gray-500">{Math.round(musicVolume * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={musicVolume}
              onChange={(e) => handleMusicVolumeChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-500"
            />
          </div>
        </div>
      </div>
    );
  }

  // ─── Floating variant (in-game) ─────────────────────────────────
  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center text-lg hover:bg-white/30 transition"
        title="Réglages du son"
      >
        {icon}
      </button>

      {open && (
        <div className="absolute right-0 top-12 z-50 bg-white rounded-xl shadow-2xl p-4 w-64 border border-gray-200">
          <h3 className="text-sm font-bold text-gray-700 mb-3">Volume</h3>

          {/* Mute */}
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-gray-600">Son</span>
            <button
              onClick={handleMuteToggle}
              className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                !muted ? 'bg-primary-500' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${
                  !muted ? 'translate-x-4' : 'translate-x-0.5'
                }`}
              />
            </button>
          </div>

          {/* Effects */}
          <div className="mb-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-600">Effets</span>
              <span className="text-xs text-gray-400">{Math.round(effectsVolume * 100)}%</span>
            </div>
            <input
              type="range" min="0" max="1" step="0.05"
              value={effectsVolume}
              onChange={(e) => handleEffectsVolumeChange(parseFloat(e.target.value))}
              disabled={muted}
              className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-500 disabled:opacity-50"
            />
          </div>

          {/* Music */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-600">Musique</span>
              <span className="text-xs text-gray-400">{Math.round(musicVolume * 100)}%</span>
            </div>
            <input
              type="range" min="0" max="1" step="0.05"
              value={musicVolume}
              onChange={(e) => handleMusicVolumeChange(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-500"
            />
          </div>
        </div>
      )}
    </div>
  );
}
