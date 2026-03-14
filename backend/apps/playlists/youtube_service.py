"""YouTube Data API v3 service for searching playlists and videos.

Music streaming service integration for InstantMusic.
"""

import logging
import re
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

from .base_api_service import BaseAPIService

logger = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────────────

CACHE_TTL_SEARCH: int = 1800  # 30 min for search results
CACHE_TTL_DETAIL: int = 3600  # 1 hour for playlist / track details

# Pre-compiled regex for stripping video-title suffixes (Official Video, etc.)
_SUFFIX_RE = re.compile(
    r"\s*[\(\[\|]?\s*(?:official\s+)?(?:music\s+)?(?:video|lyric|lyrics|audio|clip|hd|4k|visualizer|visualiser|mv|feat\.?|ft\.?).*$",
    flags=re.IGNORECASE,
)

_ISO_DURATION_RE = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def _extract_thumbnail_url(snippet: dict[str, Any]) -> str:
    """Extrait l'URL de la meilleure miniature (high > medium > default)."""
    thumbnails = snippet.get("thumbnails", {})
    url: str = (
        thumbnails.get("high", {}).get("url")
        or thumbnails.get("medium", {}).get("url")
        or thumbnails.get("default", {}).get("url", "")
    )
    return url


class YouTubeAPIError(Exception):
    """Custom exception for YouTube API errors."""

    pass


class YouTubeService(BaseAPIService):
    """Service to interact with YouTube Data API v3.

    Uses API key authentication (no OAuth needed).
    Provides playlist search, video search, and playlist item listing.
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3"
    _error_class = YouTubeAPIError

    def __init__(self) -> None:
        self.api_key = getattr(settings, "YOUTUBE_API_KEY", "")

    def _extract_http_error_message(self, e: requests.exceptions.HTTPError) -> str:
        """Extrait les détails d'erreur du corps JSON de la réponse YouTube."""
        try:
            return e.response.json().get("error", {}).get("message", "") or str(e)
        except Exception:
            return str(e)

    def _make_request(self, endpoint: str, params: dict) -> dict:
        """Make a request to the YouTube Data API.

        Args:
            endpoint: API endpoint (e.g., 'search', 'playlists', 'playlistItems')
            params: Query parameters

        Returns:
            JSON response dict

        Raises:
            YouTubeAPIError: If the request fails

        """
        if not self.api_key:
            raise YouTubeAPIError(
                "YouTube API key not configured. Set YOUTUBE_API_KEY in settings."
            )

        params["key"] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"
        return self._get_json(url, params)

    def search_playlists(self, query: str, limit: int = 20) -> list[dict]:
        """Search for music playlists on YouTube.

        Args:
            query: Search query
            limit: Max results (max 50)

        Returns:
            List of playlist dicts

        """
        cache_key = f"yt_search_pl_{query}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached  # type: ignore[no-any-return]

        params = {
            "part": "snippet",
            "q": f"{query} music",
            "type": "playlist",
            "maxResults": min(limit, 50),
        }

        try:
            data = self._make_request("search", params)
        except YouTubeAPIError:
            return []

        playlists = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            playlist_id = item.get("id", {}).get("playlistId", "")
            if not playlist_id:
                continue

            image_url = _extract_thumbnail_url(snippet)

            playlists.append(
                {
                    "playlist_id": playlist_id,
                    "name": snippet.get("title", ""),
                    "description": snippet.get("description", ""),
                    "image_url": image_url,
                    "owner": snippet.get("channelTitle", ""),
                    "external_url": f"https://www.youtube.com/playlist?list={playlist_id}",
                }
            )

        cache.set(cache_key, playlists, CACHE_TTL_SEARCH)
        return playlists

    def get_playlist(self, playlist_id: str) -> dict | None:
        """Get playlist details by ID.

        Args:
            playlist_id: YouTube playlist ID

        Returns:
            Playlist dict or None

        """
        cache_key = f"yt_playlist_{playlist_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached  # type: ignore[no-any-return]

        params = {
            "part": "snippet,contentDetails",
            "id": playlist_id,
        }

        try:
            data = self._make_request("playlists", params)
        except YouTubeAPIError:
            return None

        items = data.get("items", [])
        if not items:
            return None

        item = items[0]
        snippet = item.get("snippet", {})
        content = item.get("contentDetails", {})
        image_url = _extract_thumbnail_url(snippet)

        result = {
            "playlist_id": playlist_id,
            "name": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "image_url": image_url,
            "total_tracks": content.get("itemCount", 0),
            "owner": snippet.get("channelTitle", ""),
            "external_url": f"https://www.youtube.com/playlist?list={playlist_id}",
        }

        cache.set(cache_key, result, CACHE_TTL_DETAIL)
        return result

    def get_playlist_tracks(self, playlist_id: str, limit: int = 50) -> list[dict]:
        """Get videos from a YouTube playlist.

        Args:
            playlist_id: YouTube playlist ID
            limit: Max videos to return

        Returns:
            List of track dicts

        """
        cache_key = f"yt_pl_tracks_{playlist_id}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached  # type: ignore[no-any-return]

        all_items: list[dict[str, Any]] = []
        next_page_token = None

        while len(all_items) < limit:
            params = {
                "part": "snippet,contentDetails",
                "playlistId": playlist_id,
                "maxResults": min(50, limit - len(all_items)),
            }
            if next_page_token:
                params["pageToken"] = next_page_token

            try:
                data = self._make_request("playlistItems", params)
            except YouTubeAPIError as e:
                logger.warning(
                    "Failed to get playlist items for %s: %s", playlist_id, e
                )
                break

            items = data.get("items", [])
            if not items:
                break

            all_items.extend(items)
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break

        # Now get video details (duration, etc.) for all video IDs
        video_ids = []
        for item in all_items:
            vid_id = item.get("contentDetails", {}).get("videoId")
            if vid_id:
                video_ids.append(vid_id)

        video_details = self._get_video_details(video_ids) if video_ids else {}

        tracks = []
        for item in all_items:
            snippet = item.get("snippet", {})
            vid_id = item.get("contentDetails", {}).get("videoId")

            if not vid_id:
                continue

            # Skip deleted/private videos
            title = snippet.get("title", "")
            if title in ("Deleted video", "Private video", ""):
                continue

            image_url = _extract_thumbnail_url(snippet)

            # Parse artist and title from video title
            artist, track_name = self._parse_video_title(title)

            details = video_details.get(vid_id, {})
            duration_ms = details.get("duration_ms", 0)
            embeddable = details.get("embeddable", True)

            # Skip non-embeddable videos (they won't play in the iframe player)
            if not embeddable:
                logger.debug(
                    "Skipping non-embeddable video: %s (%s)",
                    vid_id,
                    track_name,
                )
                continue

            tracks.append(
                {
                    "track_id": vid_id,
                    "name": track_name,
                    "artists": [artist],
                    "album": snippet.get("videoOwnerChannelTitle", "YouTube"),
                    "album_image": image_url,
                    "duration_ms": duration_ms,
                    # YouTube doesn't have preview URLs - we use the iframe player
                    "preview_url": None,
                    "external_url": f"https://www.youtube.com/watch?v={vid_id}",
                }
            )

        cache.set(cache_key, tracks, CACHE_TTL_DETAIL)
        return tracks[:limit]

    def search_music_videos(self, query: str, limit: int = 50) -> list[dict]:
        """Search for music videos on YouTube.

        Useful as a fallback when playlist access fails.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of track dicts

        """
        cache_key = f"yt_search_vid_{query}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached  # type: ignore[no-any-return]

        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "videoCategoryId": "10",  # Music category
            "maxResults": min(limit, 50),
        }

        try:
            data = self._make_request("search", params)
        except YouTubeAPIError:
            return []

        video_ids = []
        items_map = {}
        for item in data.get("items", []):
            vid_id = item.get("id", {}).get("videoId", "")
            if vid_id:
                video_ids.append(vid_id)
                items_map[vid_id] = item

        video_details = self._get_video_details(video_ids) if video_ids else {}

        tracks = []
        for vid_id in video_ids:
            item = items_map[vid_id]
            snippet = item.get("snippet", {})
            title = snippet.get("title", "")

            image_url = _extract_thumbnail_url(snippet)

            artist, track_name = self._parse_video_title(title)
            details = video_details.get(vid_id, {})
            duration_ms = details.get("duration_ms", 0)

            tracks.append(
                {
                    "track_id": vid_id,
                    "name": track_name,
                    "artists": [artist],
                    "album": snippet.get("channelTitle", "YouTube"),
                    "album_image": image_url,
                    "duration_ms": duration_ms,
                    "preview_url": None,
                    "external_url": f"https://www.youtube.com/watch?v={vid_id}",
                }
            )

        cache.set(cache_key, tracks, CACHE_TTL_SEARCH)
        return tracks

    def _get_video_details(self, video_ids: list[str]) -> dict[str, dict]:
        """Get video details (duration, etc.) for multiple videos.

        Args:
            video_ids: List of YouTube video IDs

        Returns:
            Dict mapping video_id to details

        """
        details = {}

        # Process in batches of 50
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i : i + 50]
            params = {
                "part": "contentDetails,status",
                "id": ",".join(batch),
            }

            try:
                data = self._make_request("videos", params)
            except YouTubeAPIError:
                continue

            for item in data.get("items", []):
                vid_id = item.get("id", "")
                content = item.get("contentDetails", {})
                status = item.get("status", {})
                duration_iso = content.get("duration", "PT0S")
                duration_ms = self._parse_iso_duration(duration_iso)
                embeddable = status.get("embeddable", True)
                details[vid_id] = {
                    "duration_ms": duration_ms,
                    "embeddable": embeddable,
                }

        return details

    @staticmethod
    def _parse_iso_duration(duration: str) -> int:
        """Parse ISO 8601 duration to milliseconds.

        Example: 'PT4M13S' -> 253000.
        """
        match = _ISO_DURATION_RE.match(duration)
        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return (hours * 3600 + minutes * 60 + seconds) * 1000

    @staticmethod
    def _parse_video_title(title: str) -> tuple:
        """Parse a YouTube music video title into artist and track name.

        Common formats:
        - "Artist - Track Name"
        - "Artist - Track Name (Official Video)"
        - "Artist - Track Name [Official Music Video]"
        - "Title (Official Video) - Artist"  ← inverted order, still handled

        Returns:
            Tuple of (artist, track_name)

        """

        def _strip(s: str) -> str:
            return _SUFFIX_RE.sub("", s).strip()

        # ── Step 1: try to split the ORIGINAL title (before any stripping) ──
        # This preserves the artist when it comes AFTER a parenthetical suffix,
        # e.g. "Sarà perché ti amo (Official Video) - Ricchi e Poveri".
        for sep in [" - ", " – ", " — ", " | ", " // "]:
            if sep in title:
                parts = title.split(sep, 1)
                return _strip(parts[0]), _strip(parts[1])

        # ── Step 2: no separator found — strip suffix and return whole title ──
        return "Artiste inconnu", _strip(title)


# Singleton instance
youtube_service = YouTubeService()
