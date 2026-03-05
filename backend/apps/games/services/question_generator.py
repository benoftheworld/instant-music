"""
Service de génération de questions à partir de playlists Deezer.
"""

import hashlib
import logging
import random
import re
from typing import Dict, List, Optional

import requests
from django.core.cache import cache

from apps.playlists.deezer_service import deezer_service, DeezerAPIError
from apps.playlists.youtube_service import youtube_service, YouTubeAPIError
from apps.core.prometheus_metrics import (
    EXTERNAL_API_REQUESTS_TOTAL,
    EXTERNAL_API_ERRORS_TOTAL,
    EXTERNAL_API_DURATION_SECONDS,
)
from ..models import GameMode
from ..lyrics_service import (
    get_lyrics,
    create_lyrics_question,
    get_synced_lyrics,
)
from .scoring import (
    MUSICBRAINZ_API_BASE,
    MUSICBRAINZ_USER_AGENT,
    MUSICBRAINZ_API_TIMEOUT,
    CACHE_TTL_MUSICBRAINZ,
)

logger = logging.getLogger(__name__)


class QuestionGeneratorService:
    """Service to generate quiz questions from Deezer music playlists."""

    QUESTION_TYPES = [
        "guess_title",
        "guess_artist",
        "guess_year",
        "lyrics",
        "karaoke",
    ]

    def __init__(self):
        self.deezer = deezer_service

    # ─── Helpers : année originale (MusicBrainz) ─────────────────────

    @staticmethod
    def _get_musicbrainz_year(artist: str, title: str) -> Optional[int]:
        """
        Query MusicBrainz for the earliest known release year of a recording.

        Uses the free MusicBrainz search API (no auth required).
        Results are cached for 24 h to avoid hammering the service.
        Returns the year as int, or None if the lookup fails.
        """
        cache_key = (
            "mb_year_" + hashlib.md5(f"{artist}|{title}".encode()).hexdigest()
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[no-any-return]

        try:
            # Escape special Lucene characters in the query strings
            def _esc(s: str) -> str:
                return re.sub(r'([+\-&|!(){}\[\]^"~*?:\\/])', r"\\\1", s)

            query = f'recording:"{_esc(title)}" AND artist:"{_esc(artist)}"'
            resp = requests.get(
                f"{MUSICBRAINZ_API_BASE}/recording/",
                params={"query": query, "fmt": "json", "limit": 100},  # type: ignore[arg-type]
                headers={"User-Agent": MUSICBRAINZ_USER_AGENT},
                timeout=MUSICBRAINZ_API_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "MusicBrainz lookup failed for '%s – %s': %s",
                artist,
                title,
                exc,
            )
            cache.set(cache_key, None, CACHE_TTL_MUSICBRAINZ)
            return None

        # Only consider recordings with a high relevance score (≥ 85) to
        # avoid unrelated tracks from polluting the earliest-year detection.
        years: list[int] = []
        for rec in data.get("recordings", []):
            if rec.get("score", 0) < 85:
                continue
            frd = rec.get("first-release-date", "")
            if frd and len(frd) >= 4:
                try:
                    y = int(frd[:4])
                    if 1900 <= y <= 2030:
                        years.append(y)
                except ValueError:
                    pass

        result: Optional[int] = min(years) if years else None
        cache.set(cache_key, result, CACHE_TTL_MUSICBRAINZ)
        logger.debug(
            "MusicBrainz year for '%s – %s': %s", artist, title, result
        )
        return result

    # ─── Public entry point ──────────────────────────────────────────

    def generate_questions(
        self,
        playlist_id: str,
        num_questions: int = 10,
        question_type: str = "guess_title",
        game_mode: str = "classique",
        user=None,
        lyrics_words_count: int = 3,
        guess_target: str = "title",
    ) -> List[Dict]:
        """
        Generate quiz questions from a Deezer playlist.

        Args:
            playlist_id: Deezer playlist ID
            num_questions: Number of questions to generate
            question_type: Type of question
            game_mode: The game mode (determines generator)
            user: Django user (unused, kept for compat)
            lyrics_words_count: Number of words to blank in lyrics mode
            guess_target: 'artist' or 'title' for MCQ in classique/rapide

        Returns:
            List of question dictionaries
        """
        tracks = self._fetch_tracks(playlist_id, limit=50)

        random.shuffle(tracks)
        selected_tracks = tracks[
            : min(num_questions * 2, len(tracks))
        ]  # extra buffer

        questions: List[Dict] = []

        for track in selected_tracks:
            if len(questions) >= num_questions:
                break

            question = self._generate_for_mode(
                game_mode,
                track,
                tracks,
                lyrics_words_count=lyrics_words_count,
                guess_target=guess_target,
            )
            if question:
                questions.append(question)

        return questions

    # ─── Track fetching (shared) ─────────────────────────────────────

    def _fetch_tracks(self, playlist_id: str, limit: int = 50) -> List[Dict]:
        """Fetch tracks from Deezer playlist with fallback."""
        import time as _time

        EXTERNAL_API_REQUESTS_TOTAL.labels(
            service="deezer", endpoint="get_playlist_tracks"
        ).inc()
        _t0 = _time.monotonic()
        try:
            logger.info("Fetching tracks from Deezer playlist %s", playlist_id)
            tracks = self.deezer.get_playlist_tracks(playlist_id, limit=limit)
            EXTERNAL_API_DURATION_SECONDS.labels(service="deezer").observe(
                _time.monotonic() - _t0
            )
        except DeezerAPIError as e:
            EXTERNAL_API_DURATION_SECONDS.labels(service="deezer").observe(
                _time.monotonic() - _t0
            )
            EXTERNAL_API_ERRORS_TOTAL.labels(
                service="deezer", error_type="api_error"
            ).inc()
            logger.error(
                "Failed to get tracks from Deezer playlist %s: %s",
                playlist_id,
                e,
            )
            raise ValueError(
                f"Erreur lors de l'accès à la playlist Deezer: {e}"
            )

        if not tracks or len(tracks) < 4:
            found = len(tracks) if tracks else 0
            logger.warning(
                "Deezer playlist %s returned %d tracks, attempting fallback",
                playlist_id,
                found,
            )

            try:
                EXTERNAL_API_REQUESTS_TOTAL.labels(
                    service="deezer", endpoint="get_playlist"
                ).inc()
                meta = self.deezer.get_playlist(playlist_id)
                query = (
                    meta["name"] if meta and meta.get("name") else playlist_id
                )
            except Exception:
                query = playlist_id

            try:
                EXTERNAL_API_REQUESTS_TOTAL.labels(
                    service="deezer", endpoint="search_music_videos"
                ).inc()
                fallback = self.deezer.search_music_videos(query, limit=limit)
            except Exception as e:
                logger.error("Fallback search failed: %s", e)
                fallback = []

            if fallback and len(fallback) >= 4:
                tracks = fallback
            else:
                raise ValueError(
                    f"La playlist ne contient pas assez de morceaux "
                    f"({found} trouvés, minimum 4 requis)."
                )

        return tracks

    # ─── Mode dispatcher ─────────────────────────────────────────────

    def _generate_for_mode(
        self,
        game_mode: str,
        track: Dict,
        all_tracks: List[Dict],
        lyrics_words_count: int = 3,
        guess_target: str = "title",
    ) -> Optional[Dict]:
        """Route to the correct question generator based on game mode."""
        if game_mode == GameMode.CLASSIQUE:
            if guess_target == "artist":
                return self._generate_guess_artist_question(track, all_tracks)
            else:
                return self._generate_guess_title_question(track, all_tracks)
        elif game_mode == GameMode.RAPIDE:
            if guess_target == "artist":
                q = self._generate_guess_artist_question(track, all_tracks)
            else:
                q = self._generate_guess_title_question(track, all_tracks)
            if q:
                q["extra_data"] = q.get("extra_data", {})
                q["extra_data"]["audio_duration"] = 3
            return q
        elif game_mode == GameMode.GENERATION:
            return self._generate_year_question(track)
        elif game_mode == GameMode.PAROLES:
            return self._generate_lyrics_question(
                track, all_tracks, words_to_blank=lyrics_words_count
            )
        elif game_mode == GameMode.KARAOKE:
            return self._generate_karaoke_question(track, all_tracks)
        else:
            return self._generate_guess_title_question(track, all_tracks)

    # ─── Quiz 4 (default) ────────────────────────────────────────────

    def _generate_guess_title_question(
        self, correct_track: Dict, all_tracks: List[Dict]
    ) -> Optional[Dict]:
        """Generate a 'guess the title' question."""
        correct_answer = correct_track["name"]
        wrong_answers = self._pick_wrong_answers(
            correct_track, all_tracks, key="name", count=3
        )
        if len(wrong_answers) < 3:
            return None

        options = [correct_answer] + wrong_answers[:3]
        random.shuffle(options)

        return {
            "track_id": correct_track["track_id"],
            "track_name": correct_track["name"],
            "artist_name": ", ".join(correct_track["artists"]),
            "preview_url": correct_track.get("preview_url"),
            "album_image": correct_track.get("album_image"),
            "question_type": "guess_title",
            "question_text": "Quel est le titre de ce morceau ?",
            "correct_answer": correct_answer,
            "options": options,
            "extra_data": {},
        }

    def _generate_guess_artist_question(
        self, correct_track: Dict, all_tracks: List[Dict]
    ) -> Optional[Dict]:
        """Generate a 'guess the artist' question."""
        correct_answer = ", ".join(correct_track["artists"])
        other_tracks = [
            t for t in all_tracks if t["track_id"] != correct_track["track_id"]
        ]
        random.shuffle(other_tracks)

        wrong_answers = []
        for track in other_tracks:
            artist = ", ".join(track["artists"])
            if artist != correct_answer and artist not in wrong_answers:
                wrong_answers.append(artist)
            if len(wrong_answers) >= 3:
                break

        if len(wrong_answers) < 3:
            return None

        options = [correct_answer] + wrong_answers[:3]
        random.shuffle(options)

        return {
            "track_id": correct_track["track_id"],
            "track_name": correct_track["name"],
            "artist_name": correct_answer,
            "preview_url": correct_track.get("preview_url"),
            "album_image": correct_track.get("album_image"),
            "question_type": "guess_artist",
            "question_text": "Qui interprète ce morceau ?",
            "correct_answer": correct_answer,
            "options": options,
            "extra_data": {},
        }

    # ─── Année de Sortie ─────────────────────────────────────────────

    def _generate_year_question(self, track: Dict) -> Optional[Dict]:
        """Player guesses the release year (±2 tolerance)."""
        track_id = track["track_id"]

        # Get detailed info including release_date
        EXTERNAL_API_REQUESTS_TOTAL.labels(
            service="deezer", endpoint="get_track_details"
        ).inc()
        details = self.deezer.get_track_details(track_id)
        if not details or not details.get("release_date"):
            return None

        release_date = details["release_date"]  # "YYYY-MM-DD"
        try:
            year = int(release_date[:4])
        except (ValueError, IndexError):
            return None

        if year < 1900 or year > 2030:
            return None

        # ── Recherche systématique de l'année originale (MusicBrainz) ─
        artist_name = ", ".join(track["artists"])
        EXTERNAL_API_REQUESTS_TOTAL.labels(
            service="musicbrainz", endpoint="recording_search"
        ).inc()
        mb_year = self._get_musicbrainz_year(artist_name, track["name"])
        if mb_year and mb_year < year:
            logger.info(
                "Année corrigée via MusicBrainz pour '%s – %s': %d → %d",
                artist_name,
                track["name"],
                year,
                mb_year,
            )
            year = mb_year
            release_date = str(mb_year)

        # Generate MCQ options (4 plausible years)
        options = [str(year)]
        attempts = 0
        while len(options) < 4 and attempts < 30:
            offset = random.choice(
                [
                    -10,
                    -8,
                    -7,
                    -6,
                    -5,
                    -4,
                    -3,
                    -2,
                    -1,
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    10,
                ]
            )
            wrong_year = year + offset
            if str(wrong_year) not in options and 1900 <= wrong_year <= 2030:
                options.append(str(wrong_year))
            attempts += 1
        random.shuffle(options)

        artist = ", ".join(track["artists"])
        return {
            "track_id": track_id,
            "track_name": track["name"],
            "artist_name": artist,
            "preview_url": track.get("preview_url"),
            "album_image": track.get("album_image"),
            "question_type": "guess_year",
            "question_text": f'En quelle année est sorti « {track["name"]} » de {artist} ?',
            "correct_answer": str(year),
            "options": options,
            "extra_data": {
                "release_date": release_date,
                "year": year,
                "tolerance": 2,
            },
        }

    # ─── Lyrics ──────────────────────────────────────────────────────

    def _generate_lyrics_question(
        self, track: Dict, all_tracks: List[Dict], words_to_blank: int = 1
    ) -> Optional[Dict]:
        """Fetch lyrics, extract a line, blank out a sequence of words."""
        artist = ", ".join(track["artists"])
        lyrics = get_lyrics(artist, track["name"])

        if not lyrics:
            logger.warning(
                "No lyrics found for %s – %s, skipping track",
                artist,
                track["name"],
            )
            return None

        # Collect extra words from other track titles for wrong options
        extra_words = []
        for t in all_tracks:
            extra_words.extend(re.findall(r"[a-zA-ZÀ-ÿ\'-]{3,}", t["name"]))

        result = create_lyrics_question(lyrics, extra_words, words_to_blank)
        if not result:
            logger.warning(
                "Failed to create lyrics question for %s – %s, skipping track",
                artist,
                track["name"],
            )
            return None

        snippet, correct_word, options = result

        return {
            "track_id": track["track_id"],
            "track_name": track["name"],
            "artist_name": artist,
            "preview_url": track.get("preview_url"),
            "album_image": track.get("album_image"),
            "question_type": "lyrics",
            "question_text": f'Complétez les paroles de « {track["name"]} » :',
            "correct_answer": correct_word,
            "options": options,
            "extra_data": {
                "lyrics_snippet": snippet,
            },
        }

    # ─── Karaoké ─────────────────────────────────────────────────────

    def _generate_karaoke_question(
        self, track: Dict, all_tracks: List[Dict]
    ) -> Optional[Dict]:
        """Generate a karaoke round: YouTube full-song playback + synced lyrics."""
        artist = ", ".join(track["artists"])

        # 1. Synced lyrics are required for karaoke
        synced, _ = get_synced_lyrics(artist, track["name"])
        if not synced:
            logger.warning(
                "No synced lyrics for %s – %s, skipping karaoke",
                artist,
                track["name"],
            )
            return None

        # 2. Find the YouTube video for full playback
        youtube_video_id = None
        video_duration_ms = 0
        album_image = track.get("album_image", "")

        if not youtube_video_id:
            try:
                EXTERNAL_API_REQUESTS_TOTAL.labels(
                    service="youtube", endpoint="search_music_videos"
                ).inc()
                results = youtube_service.search_music_videos(
                    f"{artist} {track['name']}", limit=3
                )
                if results:
                    youtube_video_id = results[0]["track_id"]
                    video_duration_ms = results[0].get("duration_ms", 0)
                    if results[0].get("album_image"):
                        album_image = results[0]["album_image"]
            except YouTubeAPIError as e:
                logger.warning("YouTube search failed for karaoke: %s", e)

        if not youtube_video_id:
            logger.warning(
                "No YouTube video found for %s – %s, skipping karaoke",
                artist,
                track["name"],
            )
            return None

        extra_data: Dict = {
            "synced_lyrics": synced,
            "youtube_video_id": youtube_video_id,
            "video_duration_ms": video_duration_ms,
        }

        return {
            "track_id": track["track_id"],
            "track_name": track["name"],
            "artist_name": artist,
            "preview_url": "",  # Not used — YouTube player handles audio
            "album_image": track.get("album_image"),
            "question_type": "karaoke",
            "question_text": f"{track['name']} — {artist}",
            "correct_answer": track["name"],  # Stored for display only
            "options": [],  # No MCQ in karaoke
            "extra_data": extra_data,
        }

    # ─── Helpers ─────────────────────────────────────────────────────

    def _pick_wrong_answers(
        self,
        correct_track: Dict,
        all_tracks: List[Dict],
        key: str = "name",
        count: int = 3,
    ) -> List[str]:
        """Pick distinct wrong answers from the track pool."""
        correct_val = correct_track[key]
        other = [
            t for t in all_tracks if t["track_id"] != correct_track["track_id"]
        ]
        random.shuffle(other)

        wrong = []
        for t in other:
            val = t[key] if isinstance(t[key], str) else ", ".join(t[key])
            if val != correct_val and val not in wrong:
                wrong.append(val)
            if len(wrong) >= count:
                break
        return wrong


# Singleton
question_generator_service = QuestionGeneratorService()
