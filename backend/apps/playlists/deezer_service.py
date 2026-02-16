"""
Deezer API service for searching playlists and tracks.
Replaces YouTube as the music source — uses free 30-second MP3 previews.
No API key required.
"""
import logging
import random
import hashlib
from typing import Dict, List, Optional

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)


class DeezerAPIError(Exception):
    """Custom exception for Deezer API errors."""
    pass


class DeezerService:
    """
    Service to interact with the Deezer public API.

    Provides playlist search, track search, and playlist track listing.
    All tracks include a direct 30-second MP3 preview URL.
    """

    BASE_URL = "https://api.deezer.com"

    def _make_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """
        Make a GET request to the Deezer API.

        Args:
            endpoint: API path (e.g., '/search/playlist')
            params: Query parameters

        Returns:
            JSON response dict

        Raises:
            DeezerAPIError: If the request fails
        """
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = requests.get(url, params=params or {}, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Deezer returns errors in the JSON body
            if "error" in data:
                error_msg = data["error"].get("message", "Unknown Deezer error")
                raise DeezerAPIError(f"Deezer API error: {error_msg}")

            return data
        except requests.exceptions.HTTPError as e:
            logger.error("Deezer API HTTP error on %s: %s", endpoint, e)
            raise DeezerAPIError(f"Deezer API HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error("Deezer API request failed: %s", e)
            raise DeezerAPIError(f"Deezer API request failed: {e}")

    # ── Playlist operations ──────────────────────────────────────────

    def search_playlists(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for playlists on Deezer.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of playlist dicts with keys:
            youtube_id (kept for compat, actually deezer id), name, description,
            image_url, total_tracks, owner, external_url
        """
        cache_key = f"dz_search_pl_{hashlib.md5(query.encode()).hexdigest()}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        data = self._make_request("/search/playlist", {"q": query, "limit": limit})

        playlists = []
        for item in data.get("data", []):
            playlists.append({
                "youtube_id": str(item["id"]),  # kept for interface compat
                "name": item.get("title", ""),
                "description": "",
                "image_url": item.get("picture_medium", item.get("picture", "")),
                "total_tracks": item.get("nb_tracks", 0),
                "owner": item.get("user", {}).get("name", "Deezer"),
                "external_url": item.get("link", ""),
            })

        cache.set(cache_key, playlists, 3600)  # cache 1 hour
        return playlists

    def get_playlist(self, playlist_id: str) -> Optional[Dict]:
        """
        Get a single playlist by Deezer ID.

        Returns:
            Playlist dict or None
        """
        cache_key = f"dz_pl_{playlist_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            data = self._make_request(f"/playlist/{playlist_id}")
        except DeezerAPIError:
            return None

        playlist = {
            "youtube_id": str(data["id"]),
            "name": data.get("title", ""),
            "description": data.get("description", ""),
            "image_url": data.get("picture_medium", data.get("picture", "")),
            "total_tracks": data.get("nb_tracks", 0),
            "owner": data.get("creator", {}).get("name", "Deezer"),
            "external_url": data.get("link", ""),
        }

        cache.set(cache_key, playlist, 3600)
        return playlist

    def get_playlist_tracks(self, playlist_id: str, limit: int = 50) -> List[Dict]:
        """
        Get tracks from a Deezer playlist.
        Filters out tracks without a preview URL.

        Args:
            playlist_id: Deezer playlist ID
            limit: Max tracks to return

        Returns:
            List of track dicts
        """
        cache_key = f"dz_pl_tracks_{playlist_id}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        tracks = []
        # Deezer paginates tracks, fetch in batches
        index = 0
        batch_size = 100  # Deezer max per request

        while len(tracks) < limit:
            try:
                data = self._make_request(
                    f"/playlist/{playlist_id}/tracks",
                    {"limit": batch_size, "index": index},
                )
            except DeezerAPIError as e:
                if not tracks:
                    raise
                break

            items = data.get("data", [])
            if not items:
                break

            for item in items:
                track = self._parse_track(item)
                if track:  # only tracks with preview
                    tracks.append(track)

            # Check if there are more pages
            if "next" not in data:
                break
            index += batch_size

        # Trim to limit
        tracks = tracks[:limit]

        if tracks:
            cache.set(cache_key, tracks, 1800)  # cache 30 min

        return tracks

    def search_tracks(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for tracks on Deezer.

        Args:
            query: Search query (e.g., 'Dua Lipa Levitating')
            limit: Max results

        Returns:
            List of track dicts (only those with preview URLs)
        """
        cache_key = f"dz_search_tr_{hashlib.md5(query.encode()).hexdigest()}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        data = self._make_request("/search", {"q": query, "limit": limit})

        tracks = []
        for item in data.get("data", []):
            track = self._parse_track(item)
            if track:
                tracks.append(track)

        if tracks:
            cache.set(cache_key, tracks, 3600)

        return tracks

    def search_music_videos(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Alias for search_tracks — interface compat with YouTubeService.
        """
        return self.search_tracks(query, limit)

    # ── Helpers ──────────────────────────────────────────────────────

    def _parse_track(self, item: dict) -> Optional[Dict]:
        """
        Parse a Deezer track item into our normalised format.
        Returns None if the track has no preview URL.

        Keys kept compatible with the existing question generator:
          youtube_id  → Deezer track id (str)
          name        → Track title
          artists     → list[str]
          album       → Album title
          album_image → Album cover URL
          preview_url → 30-second MP3 preview URL
          external_url → Link to Deezer track page
        """
        preview = item.get("preview", "")
        if not preview:
            return None

        artist = item.get("artist", {})
        album = item.get("album", {})

        return {
            "youtube_id": str(item.get("id", "")),
            "name": item.get("title", item.get("title_short", "")),
            "artists": [artist.get("name", "Unknown")],
            "album": album.get("title", ""),
            "album_image": album.get("cover_medium", album.get("cover", "")),
            "preview_url": preview,
            "external_url": item.get("link", ""),
            "duration_ms": (item.get("duration", 30)) * 1000,
        }


# Singleton
deezer_service = DeezerService()
