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

from .game_service import GameService, game_service  # noqa: F401
from .question_generator import (  # noqa: F401
    QuestionGeneratorService,
    question_generator_service,
)
from .scoring import (  # noqa: F401
    KARAOKE_FALLBACK_DURATION,
    KARAOKE_MAX_DURATION,
    MODE_CONFIG,
    RANK_BONUS,
    SCORE_BASE_POINTS,
    SCORE_MIN_CORRECT,
    SCORE_MIN_FINAL,
    SCORE_TIME_PENALTY_PER_SEC,
    calculate_streak_bonus,
)
from .text_matching import fuzzy_match, normalize_text  # noqa: F401
