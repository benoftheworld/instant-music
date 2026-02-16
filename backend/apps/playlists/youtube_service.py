"""
YouTube Data API v3 service for searching playlists and videos.
Replaces Spotify as the music source.
"""
import logging
import random
from typing import Dict, List, Optional

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class YouTubeAPIError(Exception):
    """Custom exception for YouTube API errors."""
    pass


class YouTubeService:
    """
    Service to interact with YouTube Data API v3.
    
    Uses API key authentication (no OAuth needed).
    Provides playlist search, video search, and playlist item listing.
    """
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self):
        self.api_key = getattr(settings, 'YOUTUBE_API_KEY', '')
    
    def _make_request(self, endpoint: str, params: dict) -> dict:
        """
        Make a request to the YouTube Data API.
        
        Args:
            endpoint: API endpoint (e.g., 'search', 'playlists', 'playlistItems')
            params: Query parameters
            
        Returns:
            JSON response dict
            
        Raises:
            YouTubeAPIError: If the request fails
        """
        if not self.api_key:
            raise YouTubeAPIError("YouTube API key not configured. Set YOUTUBE_API_KEY in settings.")
        
        params['key'] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_body = ""
            try:
                error_body = e.response.json().get("error", {}).get("message", "")
            except Exception:
                error_body = str(e)
            logger.error("YouTube API error on %s: %s - %s", endpoint, e, error_body)
            raise YouTubeAPIError(f"YouTube API error: {error_body or str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error("YouTube API request failed: %s", e)
            raise YouTubeAPIError(f"YouTube API request failed: {e}")
    
    def search_playlists(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for music playlists on YouTube.
        
        Args:
            query: Search query
            limit: Max results (max 50)
            
        Returns:
            List of playlist dicts
        """
        cache_key = f"yt_search_pl_{query}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
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
            
            thumbnails = snippet.get("thumbnails", {})
            image_url = (
                thumbnails.get("high", {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url", "")
            )
            
            playlists.append({
                "youtube_id": playlist_id,
                "name": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "image_url": image_url,
                "owner": snippet.get("channelTitle", ""),
                "external_url": f"https://www.youtube.com/playlist?list={playlist_id}",
            })
        
        cache.set(cache_key, playlists, 1800)  # Cache 30 min
        return playlists
    
    def get_playlist(self, playlist_id: str) -> Optional[Dict]:
        """
        Get playlist details by ID.
        
        Args:
            playlist_id: YouTube playlist ID
            
        Returns:
            Playlist dict or None
        """
        cache_key = f"yt_playlist_{playlist_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
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
        thumbnails = snippet.get("thumbnails", {})
        image_url = (
            thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or thumbnails.get("default", {}).get("url", "")
        )
        
        result = {
            "youtube_id": playlist_id,
            "name": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "image_url": image_url,
            "total_tracks": content.get("itemCount", 0),
            "owner": snippet.get("channelTitle", ""),
            "external_url": f"https://www.youtube.com/playlist?list={playlist_id}",
        }
        
        cache.set(cache_key, result, 3600)  # Cache 1 hour
        return result
    
    def get_playlist_tracks(self, playlist_id: str, limit: int = 50) -> List[Dict]:
        """
        Get videos from a YouTube playlist.
        
        Args:
            playlist_id: YouTube playlist ID
            limit: Max videos to return
            
        Returns:
            List of track dicts
        """
        cache_key = f"yt_pl_tracks_{playlist_id}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        all_items = []
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
                logger.warning("Failed to get playlist items for %s: %s", playlist_id, e)
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
            
            thumbnails = snippet.get("thumbnails", {})
            image_url = (
                thumbnails.get("high", {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url", "")
            )
            
            # Parse artist and title from video title
            artist, track_name = self._parse_video_title(title)
            
            details = video_details.get(vid_id, {})
            duration_ms = details.get("duration_ms", 0)
            
            tracks.append({
                "youtube_id": vid_id,
                "name": track_name,
                "artists": [artist],
                "album": snippet.get("videoOwnerChannelTitle", "YouTube"),
                "album_image": image_url,
                "duration_ms": duration_ms,
                "preview_url": None,  # YouTube doesn't have preview URLs - we use the iframe player
                "external_url": f"https://www.youtube.com/watch?v={vid_id}",
            })
        
        cache.set(cache_key, tracks, 3600)  # Cache 1 hour
        return tracks[:limit]
    
    def search_music_videos(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search for music videos on YouTube.
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
            return cached
        
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
            
            thumbnails = snippet.get("thumbnails", {})
            image_url = (
                thumbnails.get("high", {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url", "")
            )
            
            artist, track_name = self._parse_video_title(title)
            details = video_details.get(vid_id, {})
            duration_ms = details.get("duration_ms", 0)
            
            tracks.append({
                "youtube_id": vid_id,
                "name": track_name,
                "artists": [artist],
                "album": snippet.get("channelTitle", "YouTube"),
                "album_image": image_url,
                "duration_ms": duration_ms,
                "preview_url": None,
                "external_url": f"https://www.youtube.com/watch?v={vid_id}",
            })
        
        cache.set(cache_key, tracks, 1800)  # Cache 30 min
        return tracks
    
    def _get_video_details(self, video_ids: List[str]) -> Dict[str, Dict]:
        """
        Get video details (duration, etc.) for multiple videos.
        
        Args:
            video_ids: List of YouTube video IDs
            
        Returns:
            Dict mapping video_id to details
        """
        details = {}
        
        # Process in batches of 50
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i + 50]
            params = {
                "part": "contentDetails",
                "id": ",".join(batch),
            }
            
            try:
                data = self._make_request("videos", params)
            except YouTubeAPIError:
                continue
            
            for item in data.get("items", []):
                vid_id = item.get("id", "")
                content = item.get("contentDetails", {})
                duration_iso = content.get("duration", "PT0S")
                duration_ms = self._parse_iso_duration(duration_iso)
                details[vid_id] = {"duration_ms": duration_ms}
        
        return details
    
    @staticmethod
    def _parse_iso_duration(duration: str) -> int:
        """
        Parse ISO 8601 duration to milliseconds.
        Example: 'PT4M13S' -> 253000
        """
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return (hours * 3600 + minutes * 60 + seconds) * 1000
    
    @staticmethod
    def _parse_video_title(title: str) -> tuple:
        """
        Parse a YouTube music video title into artist and track name.
        
        Common formats:
        - "Artist - Track Name"
        - "Artist - Track Name (Official Video)"
        - "Artist - Track Name [Official Music Video]"
        - "Artist 'Track Name' Official Video"
        
        Returns:
            Tuple of (artist, track_name)
        """
        import re
        
        # Remove common suffixes
        clean = re.sub(
            r'\s*[\(\[\|]?\s*(?:official\s+)?(?:music\s+)?(?:video|lyric|lyrics|audio|clip|hd|4k|visualizer|visualiser|mv|feat\.?|ft\.?).*$',
            '',
            title,
            flags=re.IGNORECASE
        )
        clean = clean.strip()
        
        # Try splitting by common separators
        for sep in [' - ', ' – ', ' — ', ' | ', ' // ']:
            if sep in clean:
                parts = clean.split(sep, 1)
                return parts[0].strip(), parts[1].strip()
        
        # If no separator found, use the whole title as track name
        # and try to extract channel name later
        return "Artiste inconnu", clean


# Singleton instance
youtube_service = YouTubeService()
