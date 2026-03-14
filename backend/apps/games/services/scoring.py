"""Constantes et fonctions de scoring pour les parties."""

# ─── Constants ──────────────────────────────────────────

# Scoring
SCORE_BASE_POINTS: int = 100
SCORE_TIME_PENALTY_PER_SEC: int = 3
SCORE_MIN_CORRECT: int = 10
SCORE_MIN_FINAL: int = 5
RANK_BONUS: dict = {0: 10, 1: 5, 2: 2}  # correct_before → bonus points

# Win streak
SCORE_STREAK_BONUS_PER_LEVEL: int = 10
SCORE_STREAK_MAX_LEVEL: int = 5  # plafond : série 6+ = +50 pts max

# Karaoke
KARAOKE_MAX_DURATION: int = 300  # seconds
KARAOKE_FALLBACK_DURATION: int = 180  # 3 min fallback

# MusicBrainz (used for génération mode to resolve original release year)
MUSICBRAINZ_API_BASE = "https://musicbrainz.org/ws/2"
MUSICBRAINZ_USER_AGENT = (
    "InstantMusic/1.0 (https://github.com/benoftheworld/instant-music)"
)
MUSICBRAINZ_API_TIMEOUT: int = 8  # seconds (100 results can be large)
CACHE_TTL_MUSICBRAINZ: int = 86400  # 24 h

# ─── Mode → default question_type mapping ─────────────────────

from ..models import GameMode  # noqa: E402

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


def calculate_streak_bonus(streak: int) -> int:
    """Bonus additionnel par palier de série (plafonné à SCORE_STREAK_MAX_LEVEL)."""
    level = min(max(streak - 1, 0), SCORE_STREAK_MAX_LEVEL)
    return level * SCORE_STREAK_BONUS_PER_LEVEL
