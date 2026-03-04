"""
Package de services pour la logique de jeu.

Les modules sont organisés par responsabilité :
- text_matching : normalisation et comparaison fuzzy de texte
- scoring : constantes et calcul de score
- question_generator : génération de questions à partir de playlists Deezer
- game_service : orchestration du flux de jeu (start, rounds, submit, finish)

Tous les symboles publics sont réexportés ici pour compatibilité ascendante
(``from apps.games.services import game_service`` continue de fonctionner).
"""

from .text_matching import normalize_text, fuzzy_match  # noqa: F401
from .scoring import (  # noqa: F401
    SCORE_BASE_POINTS,
    SCORE_TIME_PENALTY_PER_SEC,
    SCORE_MIN_CORRECT,
    SCORE_MIN_FINAL,
    RANK_BONUS,
    KARAOKE_MAX_DURATION,
    KARAOKE_FALLBACK_DURATION,
    MODE_CONFIG,
    calculate_streak_bonus,
)
from .question_generator import (  # noqa: F401
    QuestionGeneratorService,
    question_generator_service,
)
from .game_service import GameService, game_service  # noqa: F401
