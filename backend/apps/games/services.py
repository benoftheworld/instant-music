"""
Services for game logic.
Uses Deezer API for music content (30-second MP3 previews).
"""

import json
import random
import logging
import re
import unicodedata
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from django.db import transaction

from .models import (
    Game,
    GamePlayer,
    GameRound,
    GameAnswer,
    GameStatus,
    GameMode,
    AnswerMode,
    KaraokeSong,
)
from apps.playlists.deezer_service import deezer_service, DeezerAPIError
from apps.playlists.youtube_service import youtube_service, YouTubeAPIError
from apps.achievements.services import achievement_service
from apps.core.prometheus_metrics import (
    GAMES_CREATED_TOTAL,
    GAMES_ACTIVE,
    GAMES_FINISHED_TOTAL,
    ANSWERS_TOTAL,
    ANSWER_RESPONSE_TIME,
    SCORES_EARNED,
    EXTERNAL_API_REQUESTS_TOTAL,
    EXTERNAL_API_ERRORS_TOTAL,
    EXTERNAL_API_DURATION_SECONDS,
)
from .lyrics_service import (
    get_lyrics,
    create_lyrics_question,
    get_synced_lyrics,
    get_synced_lyrics_by_lrclib_id,
)


def normalize_text(text: str) -> str:
    """Normalize text for fuzzy comparison in text answer mode."""
    text = text.lower().strip()
    # Remove accents
    text = "".join(
        c
        for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    # Remove common prefixes/articles
    for prefix in ("the ", "le ", "la ", "les ", "l'", "un ", "une ", "des "):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    # Remove punctuation
    text = re.sub(r"[^a-z0-9\s]", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fuzzy_match(
    given: str, correct: str, threshold: float = 0.8
) -> Tuple[bool, float]:
    """Compare two strings with fuzzy matching for text answer mode.

    Returns (is_match, similarity_factor) where similarity_factor is 0.0-1.0.
    """
    g = normalize_text(given)
    c = normalize_text(correct)

    if g == c:
        return True, 1.0

    # Check if one contains the other
    if g in c or c in g:
        ratio = (
            min(len(g), len(c)) / max(len(g), len(c))
            if max(len(g), len(c)) > 0
            else 0
        )
        if ratio >= threshold:
            return True, ratio

    # Levenshtein-like similarity
    if not g or not c:
        return False, 0.0

    max_len = max(len(g), len(c))
    # Simple character-based similarity
    common = sum(1 for a, b in zip(g, c) if a == b)
    similarity = common / max_len

    # Also try with edit distance approximation
    if max_len <= 30:
        # DP edit distance for short strings
        dp = list(range(len(c) + 1))
        for i in range(1, len(g) + 1):
            prev = dp[0]
            dp[0] = i
            for j in range(1, len(c) + 1):
                temp = dp[j]
                if g[i - 1] == c[j - 1]:
                    dp[j] = prev
                else:
                    dp[j] = 1 + min(prev, dp[j], dp[j - 1])
                prev = temp
        edit_dist = dp[len(c)]
        edit_similarity = 1.0 - (edit_dist / max_len)
        similarity = max(similarity, edit_similarity)

    if similarity >= threshold:
        return True, similarity

    return False, similarity


logger = logging.getLogger(__name__)


# ─── Constants (previously hardcoded) ──────────────────────────────────────────

# Scoring
SCORE_BASE_POINTS: int = 100
SCORE_TIME_PENALTY_PER_SEC: int = 3
SCORE_MIN_CORRECT: int = 10
SCORE_MIN_FINAL: int = 5
RANK_BONUS: dict = {0: 10, 1: 5, 2: 2}  # correct_before → bonus points

# Karaoke
KARAOKE_MAX_DURATION: int = 300  # seconds
KARAOKE_FALLBACK_DURATION: int = 180  # 3 min fallback


# ─── Mode → default question_type mapping ─────────────────────────────────────
MODE_CONFIG = {
    GameMode.CLASSIQUE: {
        "question_type": "guess_title",
    },
    GameMode.RAPIDE: {
        "question_type": "guess_title",
    },
    GameMode.GENERATION: {
        "question_type": "guess_year",
    },
    GameMode.PAROLES: {
        "question_type": "lyrics",
    },
    GameMode.KARAOKE: {
        "question_type": "karaoke",
    },
}


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

        if year < 1950 or year > 2030:
            return None

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
            if str(wrong_year) not in options and 1950 <= wrong_year <= 2030:
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
        """Fetch lyrics, extract a line, blank out a sequence of words (length words_to_blank), 4 MCQ options."""
        artist = ", ".join(track["artists"])
        lyrics = get_lyrics(artist, track["name"])

        if not lyrics:
            # No lyrics found — skip this track so we don't mix modes
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
        """Generate a karaoke round: YouTube full-song playback + synced lyrics.

        Solo mode — the player sings along while lyrics scroll in sync with
        the YouTube video.  No MCQ guessing.  Scoring will be powered by
        voice recognition in a future update.
        """
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


class GameService:
    """Service to manage game flow and logic."""

    def __init__(self):
        self.question_generator = QuestionGeneratorService()

    def start_game(self, game: Game) -> Tuple[Game, List[GameRound]]:
        """Start a game and generate rounds from a Deezer playlist."""
        if game.status != GameStatus.WAITING:
            raise ValueError("Game is not in waiting status")

        mode = game.mode

        # Karaoke uses a single pre-selected YouTube track, not a playlist
        if mode == GameMode.KARAOKE:
            result = self._start_karaoke_game(game)
            GAMES_CREATED_TOTAL.labels(mode=mode).inc()
            GAMES_ACTIVE.inc()
            return result

        if not game.playlist_id:
            raise ValueError("Game must have a playlist")

        questions = self._generate_questions(game)
        if not questions:
            raise ValueError("Failed to generate questions from playlist")

        with transaction.atomic():
            rounds = self._build_rounds(game, questions)

            game.status = GameStatus.IN_PROGRESS
            game.started_at = timezone.now()
            game.save()

            if rounds:
                rounds[0].started_at = timezone.now()
                rounds[0].save()

        # Métriques Prometheus
        GAMES_CREATED_TOTAL.labels(mode=mode).inc()
        GAMES_ACTIVE.inc()

        return game, rounds

    # ── start_game helpers ───────────────────────────────────────────

    def _generate_questions(self, game: Game) -> List[Dict]:
        """Fetch and tag questions for the given game."""
        num_rounds = game.num_rounds or 10
        mode = game.mode
        config = MODE_CONFIG.get(mode, MODE_CONFIG[GameMode.CLASSIQUE])

        questions = self.question_generator.generate_questions(
            game.playlist_id,
            num_questions=num_rounds,
            question_type=config["question_type"],
            game_mode=mode,
            user=game.host,
            lyrics_words_count=getattr(game, "lyrics_words_count", 3),
            guess_target=getattr(game, "guess_target", "title"),
        )

        for q in questions:
            q["_mode"] = mode

        return questions

    def _build_rounds(
        self, game: Game, questions: List[Dict]
    ) -> List[GameRound]:
        """Create GameRound objects from questions inside an atomic block."""
        num_rounds = game.num_rounds or 10
        round_duration = game.round_duration or 30
        is_text_mode = game.answer_mode == AnswerMode.TEXT
        is_karaoke = game.mode == GameMode.KARAOKE

        rounds: List[GameRound] = []
        for i, q in enumerate(questions[:num_rounds], start=1):
            round_duration_effective = self._effective_round_duration(
                q, is_karaoke, round_duration
            )
            extra_data = self._build_extra_data(q, game)
            options = self._resolve_options(q, is_karaoke, is_text_mode)

            round_obj = GameRound.objects.create(
                game=game,
                round_number=i,
                track_id=q["track_id"],
                track_name=q["track_name"],
                artist_name=q["artist_name"],
                correct_answer=q["correct_answer"],
                options=options,
                preview_url=q.get("preview_url", ""),
                question_type=q.get("question_type", "guess_title"),
                question_text=q.get("question_text", ""),
                extra_data=extra_data,
                duration=round_duration_effective,
            )
            rounds.append(round_obj)
        return rounds

    @staticmethod
    def _effective_round_duration(
        question: Dict, is_karaoke: bool, default_duration: int
    ) -> int:
        """Determine the round duration, respecting karaoke video length."""
        if is_karaoke:
            vid_dur_ms = question.get("extra_data", {}).get(
                "video_duration_ms", 0
            )
            if vid_dur_ms > 0:
                return min(vid_dur_ms // 1000 + 5, KARAOKE_MAX_DURATION)
            return KARAOKE_FALLBACK_DURATION
        return default_duration

    @staticmethod
    def _build_extra_data(question: Dict, game: Game) -> Dict:
        """Assemble the extra_data dict stored on each GameRound."""
        extra_data = question.get("extra_data", {}).copy()
        if "album_image" not in extra_data and question.get("album_image"):
            extra_data["album_image"] = question["album_image"]
        extra_data["round_mode"] = question.get("_mode", game.mode)
        extra_data["answer_mode"] = game.answer_mode
        extra_data["guess_target"] = game.guess_target
        extra_data["artist_name"] = question["artist_name"]
        extra_data["track_name"] = question["track_name"]
        return extra_data

    @staticmethod
    def _resolve_options(
        question: Dict, is_karaoke: bool, is_text_mode: bool
    ) -> list:
        """Return MCQ options or an empty list for text/karaoke modes."""
        if is_karaoke or is_text_mode:
            return []
        return question["options"]

    def _start_karaoke_game(self, game: Game) -> Tuple[Game, List[GameRound]]:
        """Start a karaoke game from the pre-selected YouTube track.

        Unlike other modes, karaoke doesn't need a Deezer playlist.
        It uses the single track stored in ``game.karaoke_track``.
        When ``karaoke_track`` contains a ``lrclib_id`` (set from the
        KaraokeSong catalogue), lyrics are fetched by ID for precision.
        """
        kt = game.karaoke_track
        if not kt or not kt.get("youtube_video_id"):
            raise ValueError(
                "Le mode karaoké nécessite un morceau YouTube sélectionné."
            )

        youtube_video_id = kt["youtube_video_id"]
        track_name = kt.get("track_name", "Unknown")
        artist_name = kt.get("artist_name", "Unknown")
        duration_ms = kt.get("duration_ms", 0)
        lrclib_id = kt.get("lrclib_id")

        # Fetch synced lyrics from LRCLib — prefer direct ID lookup when available
        synced = None
        if lrclib_id:
            synced = get_synced_lyrics_by_lrclib_id(int(lrclib_id))
            if synced:
                logger.info(
                    "Loaded %d synced lyric lines by lrclib_id=%s for %s – %s",
                    len(synced),
                    lrclib_id,
                    artist_name,
                    track_name,
                )
        if not synced:
            synced, found_lrclib_id = get_synced_lyrics(
                artist_name, track_name
            )
        else:
            found_lrclib_id = None
        if not synced:
            logger.warning(
                "No synced lyrics for karaoke track %s – %s (will play without lyrics)",
                artist_name,
                track_name,
            )
            # Allow playing without lyrics (empty list)
            synced = []
        elif not lrclib_id:
            logger.info(
                "Loaded %d synced lyric lines for karaoke track %s – %s",
                len(synced),
                artist_name,
                track_name,
            )
            # Persist the found lrclib_id so future lookups bypass search
            if found_lrclib_id and game.karaoke_song_id:
                try:
                    KaraokeSong.objects.filter(pk=game.karaoke_song_id).update(
                        lrclib_id=found_lrclib_id
                    )
                    logger.info(
                        "Saved lrclib_id=%s to KaraokeSong pk=%s (%s – %s)",
                        found_lrclib_id,
                        game.karaoke_song_id,
                        artist_name,
                        track_name,
                    )
                except Exception as exc:
                    logger.warning(
                        "Failed to save lrclib_id=%s to KaraokeSong pk=%s: %s",
                        found_lrclib_id,
                        game.karaoke_song_id,
                        exc,
                    )

        # Determine round duration from video length
        if duration_ms > 0:
            round_duration = min(duration_ms // 1000 + 5, KARAOKE_MAX_DURATION)
        else:
            round_duration = KARAOKE_FALLBACK_DURATION

        extra_data = {
            "synced_lyrics": synced,
            "youtube_video_id": youtube_video_id,
            "video_duration_ms": duration_ms,
            "round_mode": GameMode.KARAOKE,
            "answer_mode": game.answer_mode,
            "guess_target": game.guess_target,
            "artist_name": artist_name,
            "track_name": track_name,
        }

        with transaction.atomic():
            round_obj = GameRound.objects.create(
                game=game,
                round_number=1,
                track_id=youtube_video_id,
                track_name=track_name,
                artist_name=artist_name,
                correct_answer=track_name,
                options=[],
                preview_url="",
                question_type="karaoke",
                question_text=f"{track_name} — {artist_name}",
                extra_data=extra_data,
                duration=round_duration,
            )

            game.status = GameStatus.IN_PROGRESS
            game.started_at = timezone.now()
            game.num_rounds = 1
            game.save()

            round_obj.started_at = timezone.now()
            round_obj.save()

        return game, [round_obj]

    def get_current_round(self, game: Game) -> Optional[GameRound]:
        return (
            game.rounds.filter(started_at__isnull=False, ended_at__isnull=True)
            .order_by("round_number")
            .first()
        )

    def get_next_round(self, game: Game) -> Optional[GameRound]:
        return (
            game.rounds.filter(started_at__isnull=True)
            .order_by("round_number")
            .first()
        )

    def start_round(self, round_obj: GameRound) -> GameRound:
        round_obj.started_at = timezone.now()
        round_obj.save()
        return round_obj

    @transaction.atomic
    def end_round(self, round_obj: GameRound) -> GameRound:
        round_obj.ended_at = timezone.now()
        round_obj.save()
        return round_obj

    # ─── Scoring ─────────────────────────────────────────────────────

    def check_answer(
        self,
        game_mode: str,
        answer: str,
        correct_answer: str,
        extra_data: dict | None = None,
    ) -> Tuple[bool, float]:
        """
        Check answer and return (is_correct, accuracy_factor).

        Génération mode: exact=1.0, ±2=0.75, ±5=0.4, else=0.0
        Classique/Rapide text mode: try matching artist+title for double points.
        Other text mode: fuzzy matching.
        MCQ: exact match.
        """
        if game_mode == GameMode.GENERATION:
            try:
                given = int(answer)
                correct = int(correct_answer)
            except (ValueError, TypeError):
                return False, 0.0

            diff = abs(given - correct)
            if diff == 0:
                return True, 1.0
            elif diff <= 2:
                return True, 0.75
            elif diff <= 5:
                return True, 0.4
            else:
                return False, 0.0

        answer_mode = (extra_data or {}).get("answer_mode", "mcq")

        if answer_mode == AnswerMode.TEXT:
            # For classique/rapide in text mode, check if user submitted both artist+title
            if game_mode in (GameMode.CLASSIQUE, GameMode.RAPIDE):
                return self._check_classique_text_answer(
                    answer, correct_answer, extra_data
                )
            else:
                is_match, similarity = fuzzy_match(
                    answer, correct_answer, threshold=0.75
                )
                return is_match, similarity if is_match else 0.0
        else:
            # MCQ: exact match
            is_correct = answer == correct_answer
            return is_correct, 1.0 if is_correct else 0.0

    def _check_classique_text_answer(
        self, answer: str, correct_answer: str, extra_data: dict | None
    ) -> Tuple[bool, float]:
        """
        Check text answer for Classique/Rapide modes.
        The answer may be JSON {"artist": "...", "title": "..."} for double points.
        If both artist and title are correct, accuracy_factor = 2.0 (double points).
        If only the main target is correct, accuracy_factor = 1.0.
        """
        extra = extra_data or {}
        # Get artist/title from extra_data (stored at round creation time)
        round_artist = extra.get("artist_name", "")
        round_title = extra.get("track_name", "")

        try:
            parsed = json.loads(answer)
            if isinstance(parsed, dict):
                artist_answer = parsed.get("artist", "")
                title_answer = parsed.get("title", "")

                artist_ok = False
                title_ok = False

                if artist_answer and round_artist:
                    artist_ok, _ = fuzzy_match(
                        artist_answer, round_artist, threshold=0.75
                    )
                if title_answer and round_title:
                    title_ok, _ = fuzzy_match(
                        title_answer, round_title, threshold=0.75
                    )

                if artist_ok and title_ok:
                    return True, 2.0  # Double points
                elif artist_ok or title_ok:
                    return True, 1.0
                else:
                    return False, 0.0
        except (json.JSONDecodeError, TypeError):
            pass

        # Fallback: simple fuzzy match against correct_answer
        is_match, similarity = fuzzy_match(
            answer, correct_answer, threshold=0.75
        )
        return is_match, similarity if is_match else 0.0

    def calculate_score(
        self, accuracy_factor: float, response_time: float, max_time: int = 30
    ) -> int:
        """Calculate base points (Option C — Linear + Rank).

        Correct: (BASE - response_time * PENALTY) * accuracy_factor, min when correct.
        """
        if accuracy_factor <= 0.0:
            return 0
        raw = max(
            SCORE_MIN_CORRECT,
            SCORE_BASE_POINTS
            - int(response_time * SCORE_TIME_PENALTY_PER_SEC),
        )
        return max(SCORE_MIN_FINAL, int(raw * accuracy_factor))

    @transaction.atomic
    def submit_answer(
        self,
        player: GamePlayer,
        round_obj: GameRound,
        answer: str,
        response_time: float,
    ) -> GameAnswer:
        """Submit and score a player's answer."""
        game_mode = round_obj.game.mode
        is_correct, accuracy_factor = self.check_answer(
            game_mode, answer, round_obj.correct_answer, round_obj.extra_data
        )
        points = self.calculate_score(
            accuracy_factor, response_time, round_obj.duration
        )

        # Rank bonus based on answer order
        rank_bonus = 0
        if is_correct:
            correct_before = GameAnswer.objects.filter(
                round=round_obj, is_correct=True
            ).count()
            rank_bonus = RANK_BONUS.get(correct_before, 0)
            points += rank_bonus

        game_answer = GameAnswer.objects.create(
            round=round_obj,
            player=player,
            answer=answer,
            is_correct=is_correct,
            points_earned=points,
            response_time=response_time,
        )

        player.score += points
        player.save()

        # Métriques Prometheus
        ANSWERS_TOTAL.labels(
            is_correct=str(is_correct), game_mode=game_mode
        ).inc()
        ANSWER_RESPONSE_TIME.labels(game_mode=game_mode).observe(response_time)
        if points > 0:
            SCORES_EARNED.labels(game_mode=game_mode).observe(points)

        return game_answer

    @transaction.atomic
    def finish_game(self, game: Game) -> Game:
        """Finish a game and calculate final rankings.

        User-level denormalized stats (total_games_played, total_wins,
        total_points) are updated by the ``update_player_stats_on_game_finish``
        signal handler in ``games.signals``, triggered by game.save().
        """
        game.status = GameStatus.FINISHED
        game.finished_at = timezone.now()

        players = game.players.order_by("-score")
        total_rounds = game.rounds.count()

        for rank, player in enumerate(players, start=1):
            player.rank = rank
            player.save()

            correct_answers = GameAnswer.objects.filter(
                player=player,
                round__game=game,
                is_correct=True,
            ).count()
            perfect_game = total_rounds > 0 and correct_answers == total_rounds

            round_data = {"perfect_game": perfect_game}
            achievement_service.check_and_award(
                player.user, game=game, round_data=round_data
            )

        # Save last so the signal fires after ranks are set
        game.save()

        # Métriques Prometheus
        GAMES_FINISHED_TOTAL.labels(mode=game.mode).inc()
        GAMES_ACTIVE.dec()

        return game


# Singleton instances
question_generator_service = QuestionGeneratorService()
game_service = GameService()
