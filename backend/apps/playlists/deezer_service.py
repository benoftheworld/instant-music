"""Deezer API service for searching playlists and tracks.

Replaces YouTube as the music source — uses free 30-second MP3 previews.
No API key required.
"""

import hashlib
import logging
import re
from typing import Any

from django.core.cache import cache

from .base_api_service import BaseAPIService

logger = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────────────

CACHE_TTL_SEARCH: int = 1800   # 30 min for search results
CACHE_TTL_DETAIL: int = 3600   # 1 hour for playlist / track details
CACHE_TTL_PREVIEW: int = 4 * 3600  # 4 hours for track details / preview URLs

# ─── Title cleaning ──────────────────────────────────────────────────

# Matches parenthesised / bracketed / dash-separated version suffixes that
# do NOT belong to the original song title, e.g.:
#   "Bohemian Rhapsody (Remastered 2011)"
#   "Hymne à l'amour - 2020 Remaster"
#   "Ma Benz [Remasterisée]"
#   "Song Title (Deluxe Edition)"
#   "Song Title (Special Edition)"
#   "Song Title (Anniversary Edition)"
_TITLE_SUFFIX_RE = re.compile(
    r"\s*(?:"
    # parenthesised / bracketed suffix — keyword can appear before or after a year
    # e.g. (Remastered 2011)  (2011 Remaster)  [Remasterisée]  (Deluxe Edition)
    r"[\(\[]"
    r"[^\)\]]*"  # any text before the keyword (handles "2011 Remaster…")
    r"(?:remaster[a-zA-Z\u00c0-\u00ff]*|re-?issue|deluxe|super\s*deluxe|anniversary|expanded|special(?:\s*(?:edition|version))?)"
    r"[^\)\]]*"  # any text after the keyword
    r"[\)\]]"
    r"|"
    # bare dash-separated suffix: « - Remastered » « - 2020 Remaster » « - Deluxe »
    r"-\s*(?:\d{4}\s*)?(?:remaster[a-zA-Z\u00c0-\u00ff]*|re-?issue|deluxe|anniversary).*"
    r")",
    re.IGNORECASE,
)


def clean_track_title(title: str) -> str:
    """Strip remaster / re-edition suffixes from a track title.

    Handles parenthesised, bracketed and dash-separated forms — including
    cases where the year precedes or follows the keyword, and French variants.

    Examples (stripped → cleaned):
      "Bohemian Rhapsody (Remastered 2011)"   → "Bohemian Rhapsody"
      "Hymne à l'amour (Remastered)"          → "Hymne à l'amour"
      "Hymne à l'amour - 2020 Remaster"       → "Hymne à l'amour"
      "Hotel California (2013 Remaster)"      → "Hotel California"
      "Ma Benz [Remasterisée]"                → "Ma Benz"
      "Thriller (Deluxe Edition)"             → "Thriller"
      "Song - Remastered"                     → "Song"

    Examples (unchanged):
      "Emmenez-moi"      → "Emmenez-moi"
      "Starman (Live)"   → "Starman (Live)"
      "99 Problems"      → "99 Problems"
    """
    cleaned = _TITLE_SUFFIX_RE.sub("", title).strip()
    # Remove any trailing lonely dash/hyphen left after the substitution
    cleaned = re.sub(r"\s*-\s*$", "", cleaned).strip()
    return cleaned or title  # safety: never return an empty string


class DeezerAPIError(Exception):
    """Custom exception for Deezer API errors."""

    pass


class DeezerService(BaseAPIService):
    """Service to interact with the Deezer public API.

    Provides playlist search, track search, and playlist track listing.
    All tracks include a direct 30-second MP3 preview URL.
    """

    BASE_URL = "https://api.deezer.com"
    _error_class = DeezerAPIError

    def _make_request(self, endpoint: str, params: dict | None = None) -> dict:
        """Make a GET request to the Deezer API.

        Args:
            endpoint: API path (e.g., '/search/playlist')
            params: Query parameters

        Returns:
            JSON response dict

        Raises:
            DeezerAPIError: If the request fails

        """
        url = f"{self.BASE_URL}{endpoint}"
        data = self._get_json(url, params)

        # Deezer returns API-level errors in the JSON body
        if "error" in data:
            error_msg = data["error"].get("message", "Unknown Deezer error")
            raise DeezerAPIError(f"Deezer API error: {error_msg}")

        return data

    # ── Playlist operations ──────────────────────────────────────────

    def search_playlists(self, query: str, limit: int = 20) -> list[dict]:
        """Search for playlists on Deezer.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of playlist dicts with keys:
            youtube_id (kept for compat, actually deezer id), name, description,
            image_url, total_tracks, owner, external_url

        """
        _digest = hashlib.md5(query.encode(), usedforsecurity=False).hexdigest()
        cache_key = f"dz_search_pl_{_digest}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached  # type: ignore[no-any-return]

        data = self._make_request("/search/playlist", {"q": query, "limit": limit})

        playlists = []
        for item in data.get("data", []):
            playlists.append(
                {
                    "playlist_id": str(item["id"]),
                    "name": item.get("title", ""),
                    "description": "",
                    "image_url": item.get("picture_medium", item.get("picture", "")),
                    "total_tracks": item.get("nb_tracks", 0),
                    "owner": item.get("user", {}).get("name", "Deezer"),
                    "external_url": item.get("link", ""),
                }
            )

        cache.set(cache_key, playlists, CACHE_TTL_DETAIL)
        return playlists

    def get_playlist(self, playlist_id: str) -> dict | None:
        """Get a single playlist by Deezer ID.

        Returns:
            Playlist dict or None

        """
        cache_key = f"dz_pl_{playlist_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached  # type: ignore[no-any-return]

        try:
            data = self._make_request(f"/playlist/{playlist_id}")
        except DeezerAPIError:
            return None

        playlist = {
            "playlist_id": str(data["id"]),
            "name": data.get("title", ""),
            "description": data.get("description", ""),
            "image_url": data.get("picture_medium", data.get("picture", "")),
            "total_tracks": data.get("nb_tracks", 0),
            "owner": data.get("creator", {}).get("name", "Deezer"),
            "external_url": data.get("link", ""),
        }

        cache.set(cache_key, playlist, CACHE_TTL_DETAIL)
        return playlist

    def get_playlist_tracks(self, playlist_id: str, limit: int = 50) -> list[dict]:
        """Get tracks from a Deezer playlist.

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
            return cached  # type: ignore[no-any-return]

        tracks: list[dict[str, Any]] = []
        # Deezer paginates tracks, fetch in batches
        index = 0
        batch_size = 100  # Deezer max per request

        while len(tracks) < limit:
            try:
                data = self._make_request(
                    f"/playlist/{playlist_id}/tracks",
                    {"limit": batch_size, "index": index},
                )
            except DeezerAPIError:
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
            cache.set(cache_key, tracks, CACHE_TTL_PREVIEW)

        return tracks

    def search_tracks(self, query: str, limit: int = 20) -> list[dict]:
        """Search for tracks on Deezer.

        Args:
            query: Search query (e.g., 'Dua Lipa Levitating')
            limit: Max results

        Returns:
            List of track dicts (only those with preview URLs)

        """
        _digest = hashlib.md5(query.encode(), usedforsecurity=False).hexdigest()
        cache_key = f"dz_search_tr_{_digest}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached  # type: ignore[no-any-return]

        data = self._make_request("/search", {"q": query, "limit": limit})

        tracks = []
        for item in data.get("data", []):
            track = self._parse_track(item)
            if track:
                tracks.append(track)

        if tracks:
            cache.set(cache_key, tracks, CACHE_TTL_DETAIL)

        return tracks

    def search_music_videos(self, query: str, limit: int = 50) -> list[dict]:
        """Alias for search_tracks — interface compat with YouTubeService."""
        return self.search_tracks(query, limit)

    def get_track_details(self, track_id: str) -> dict | None:
        """Get detailed info for a single track, including release_date.

        Returns:
            Dict with 'release_date' (str YYYY-MM-DD) and parsed track data,
            or None on error.

        """
        cache_key = f"dz_track_{track_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached  # type: ignore[no-any-return]

        try:
            data = self._make_request(f"/track/{track_id}")
        except DeezerAPIError:
            return None

        track = self._parse_track(data)
        if track:
            # Deezer exposes release_date on the track endpoint
            track["release_date"] = data.get("release_date", "")
            cache.set(cache_key, track, CACHE_TTL_PREVIEW)

        return track

    # ── Helpers ──────────────────────────────────────────────────────

    def _parse_track(self, item: dict) -> dict | None:
        """Parse a Deezer track item into our normalised format.

        Returns None if the track has no preview URL.

        Keys:
          track_id    → Deezer track id (str)
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
            "track_id": str(item.get("id", "")),
            "name": clean_track_title(item.get("title", item.get("title_short", ""))),
            "artists": [artist.get("name", "Unknown")],
            "album": album.get("title", ""),
            "album_image": album.get("cover_medium", album.get("cover", "")),
            "preview_url": preview,
            "external_url": item.get("link", ""),
            "duration_ms": (item.get("duration", 30)) * 1000,
        }


# Singleton
deezer_service = DeezerService()
