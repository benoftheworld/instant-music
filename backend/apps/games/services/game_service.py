"""
Service principal de gestion du flux de jeu (démarrage, rounds, scoring, fin).
"""

import json
import logging
from typing import Dict, List, Optional, Tuple

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from ..models import (
    Game,
    GamePlayer,
    GameRound,
    GameAnswer,
    GameStatus,
    GameMode,
    AnswerMode,
    KaraokeSong,
)
from apps.achievements.services import achievement_service
from apps.core.prometheus_metrics import (
    GAMES_CREATED_TOTAL,
    GAMES_ACTIVE,
    GAMES_FINISHED_TOTAL,
    ANSWERS_TOTAL,
    ANSWER_RESPONSE_TIME,
    SCORES_EARNED,
    EXTERNAL_API_REQUESTS_TOTAL,
)
from ..lyrics_service import (
    get_synced_lyrics,
    get_synced_lyrics_by_lrclib_id,
)
from .scoring import (
    MODE_CONFIG,
    SCORE_BASE_POINTS,
    SCORE_TIME_PENALTY_PER_SEC,
    SCORE_MIN_CORRECT,
    SCORE_MIN_FINAL,
    RANK_BONUS,
    KARAOKE_MAX_DURATION,
    KARAOKE_FALLBACK_DURATION,
    calculate_streak_bonus,
)
from .text_matching import fuzzy_match
from .question_generator import QuestionGeneratorService

logger = logging.getLogger(__name__)


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
        """Start a karaoke game from the pre-selected YouTube track."""
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
                    answer, correct_answer, threshold=0.60
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

        Accepts:
          - Free text like "artist - title", "title - artist", or just one.
          - Legacy JSON {"artist": "...", "title": "..."}.

        Each part is matched against BOTH artist and title (order does not matter).
        Both correct → accuracy_factor 2.0 (double points).
        One correct  → accuracy_factor 1.0.
        None correct → 0.0.
        """
        extra = extra_data or {}
        round_artist = extra.get("artist_name", "")
        round_title = extra.get("track_name", "")

        # ── 1. Extract the parts the user provided ──
        parts: list[str] = []

        # Try JSON first (legacy dual-step format)
        try:
            parsed = json.loads(answer)
            if isinstance(parsed, dict):
                a = (parsed.get("artist") or "").strip()
                t = (parsed.get("title") or "").strip()
                if a:
                    parts.append(a)
                if t:
                    parts.append(t)
        except (json.JSONDecodeError, TypeError):
            pass

        # If not JSON, split by common separators (-, /, |)
        if not parts:
            for sep in (" - ", " / ", " | "):
                if sep in answer:
                    parts = [p.strip() for p in answer.split(sep, 1) if p.strip()]
                    break
            if not parts:
                parts = [answer.strip()] if answer.strip() else []

        if not parts:
            return False, 0.0

        # ── 2. Match each part against both artist and title (order-free) ──
        artist_ok = False
        title_ok = False
        threshold = 0.55  # intentionally tolerant

        for part in parts:
            if not artist_ok and round_artist:
                matched, _ = fuzzy_match(part, round_artist, threshold=threshold)
                if matched:
                    artist_ok = True
                    continue
            if not title_ok and round_title:
                matched, _ = fuzzy_match(part, round_title, threshold=threshold)
                if matched:
                    title_ok = True
                    continue

        # If a single part wasn't matched yet, try it against title too
        if not artist_ok and not title_ok and len(parts) == 1:
            part = parts[0]
            if round_title:
                title_ok, _ = fuzzy_match(part, round_title, threshold=threshold)
            if not title_ok and round_artist:
                artist_ok, _ = fuzzy_match(part, round_artist, threshold=threshold)

        if artist_ok and title_ok:
            return True, 2.0
        elif artist_ok or title_ok:
            return True, 1.0
        else:
            # Last-resort: fuzzy against the full correct_answer string
            is_match, similarity = fuzzy_match(answer, correct_answer, threshold=0.55)
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

        # Streak bonus — récompense les séries de bonnes réponses consécutives
        streak_bonus = 0
        if is_correct:
            player.consecutive_correct += 1
            streak_bonus = calculate_streak_bonus(player.consecutive_correct)
            points += streak_bonus
        else:
            player.consecutive_correct = 0

        # Bonus de boutique — double_points / max_points
        applied_bonuses: list[str] = []
        try:
            from apps.shop.services import bonus_service

            points, applied_bonuses = bonus_service.apply_score_bonuses(
                player=player,
                round_number=round_obj.round_number,
                base_points=points,
                is_correct=is_correct,
                game=round_obj.game,
            )
        except Exception:  # noqa: BLE001
            logger.exception("Erreur lors de l'application des bonus pour le joueur %s", player.id)

        game_answer = GameAnswer.objects.create(
            round=round_obj,
            player=player,
            answer=answer,
            is_correct=is_correct,
            points_earned=points,
            streak_bonus=streak_bonus,
            response_time=response_time,
        )

        player.score += points
        player.save(update_fields=["score", "consecutive_correct"])

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
        """Finish a game and calculate final rankings."""
        game.status = GameStatus.FINISHED
        game.finished_at = timezone.now()

        players = game.players.order_by("-score")
        total_rounds = game.rounds.count()

        # 1. Attribuer les rangs et précalculer round_data par joueur
        player_round_data: list[tuple] = []
        for rank, player in enumerate(players, start=1):
            player.rank = rank
            player.save()

            correct_answers = GameAnswer.objects.filter(
                player=player,
                round__game=game,
                is_correct=True,
            ).count()
            perfect_game = total_rounds > 0 and correct_answers == total_rounds
            player_round_data.append((player, {"perfect_game": perfect_game}))

        # 2. Sauvegarder la partie : déclenche le signal qui met à jour
        #    total_games_played / total_wins / total_points sur chaque User.
        game.save()

        # 3. Vérifier les achievements APRÈS la mise à jour des stats utilisateur.
        for player, round_data in player_round_data:
            player.user.refresh_from_db()
            achievement_service.check_and_award(
                player.user, game=game, round_data=round_data
            )

        # 4. Attribuer les pièces de jeu à chaque participant.
        for player in game.players.select_related("user"):
            bonus_coins = 1  # 1 pièce de participation
            if player.rank == 1 and game.mode != GameMode.KARAOKE:
                bonus_coins += 10  # +10 pièces pour une victoire
            player.user.__class__.objects.filter(pk=player.user_id).update(
                coins_balance=F("coins_balance") + bonus_coins
            )
            logger.info(
                "game_coins_awarded user=%s coins=%d (rank=%s)",
                player.user.username,
                bonus_coins,
                player.rank,
            )

        # 5. Bonus créateur de partie : +5 pièces pour l'hôte.
        game.host.__class__.objects.filter(pk=game.host_id).update(
            coins_balance=F("coins_balance") + 5
        )
        logger.info(
            "game_host_bonus_awarded host=%s game=%s",
            game.host_id,
            game.id,
        )

        # Métriques Prometheus
        GAMES_FINISHED_TOTAL.labels(mode=game.mode).inc()
        GAMES_ACTIVE.dec()

        return game


# Singleton
game_service = GameService()
