"""Broadcast service for sending real-time game updates via Django Channels.

Centralises WebSocket broadcast logic previously duplicated across
GameViewSet actions (answer, end_current_round, next_round, start).
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.renderers import JSONRenderer

from .models import Game, GameAnswer, GameRound
from .serializers import GameRoundSerializer, GameSerializer

logger = logging.getLogger(__name__)


def _serialize_to_dict(serializer: Any) -> dict[str, Any]:
    """Render a DRF serializer to a plain JSON-safe dict."""
    raw = JSONRenderer().render(serializer.data)
    return json.loads(raw)  # type: ignore[no-any-return]


def _uuid_safe(obj: Any) -> Any:
    """Convertit récursivement les UUID en str pour la sérialisation msgpack."""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _uuid_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return type(obj)(_uuid_safe(v) for v in obj)
    return obj


def _group_name(room_code: str) -> str:
    return f"game_{room_code}"


def _group_send(room_code: str, message: dict) -> None:
    """Envoie un message au group Channel en garantissant la sérialisabilité msgpack."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(_group_name(room_code), _uuid_safe(message))


# ── Helpers internes ────────────────────────────────────────────────────


def _build_player_scores(round_obj: GameRound) -> dict[str, dict[str, Any]]:
    """Build per-player score breakdown for a given round."""
    scores: dict[str, dict[str, Any]] = {}
    for ans in GameAnswer.objects.filter(round=round_obj).select_related(
        "player__user"
    ):
        scores[ans.player.user.username] = {
            "points_earned": ans.points_earned,
            "is_correct": ans.is_correct,
            "response_time": ans.response_time,
            "streak_bonus": ans.streak_bonus,
            "consecutive_correct": ans.player.consecutive_correct,
        }
    return scores


def _build_updated_players(game: Game) -> list[dict[str, Any]]:
    """Build ordered list of players with current totals."""
    return [
        {
            "id": str(p.id),
            "user": str(p.user.id),
            "username": p.user.username,
            "score": p.score,
            "rank": p.rank,
            "consecutive_correct": p.consecutive_correct,
            "is_connected": p.is_connected,
            "avatar": p.user.avatar.url if p.user.avatar else None,
        }
        for p in game.players.select_related("user").order_by("-score")
    ]


# ── Public broadcast helpers ────────────────────────────────────────────


def broadcast_player_join(room_code: str, player_data: dict, game_data: dict) -> None:
    """Notify all clients that a new player joined the room."""
    _group_send(
        room_code,
        {
            "type": "broadcast_player_join",
            "player": player_data,
            "game_data": game_data,
        },
    )


def broadcast_player_leave(room_code: str, player_data: dict, game_data: dict) -> None:
    """Notify all clients that a player left the room."""
    _group_send(
        room_code,
        {
            "type": "broadcast_player_leave",
            "player": player_data,
            "game_data": game_data,
        },
    )


def broadcast_game_update(room_code: str, game_data: dict) -> None:
    """Notify all clients of a general game state change (e.g. playlist update)."""
    _group_send(
        room_code,
        {
            "type": "broadcast_game_update",
            "game_data": game_data,
        },
    )


def broadcast_round_start(room_code: str, round_obj: GameRound) -> None:
    """Broadcast that a round has started with its data."""
    round_data = _serialize_to_dict(GameRoundSerializer(round_obj))
    _group_send(
        room_code,
        {
            "type": "broadcast_round_start",
            "round_data": round_data,
        },
    )


def broadcast_round_end(room_code: str, round_obj: GameRound, game: Game) -> None:
    """Broadcast round end with correct answer, per-player scores, and updated totals."""
    # Réinitialiser la série des joueurs qui n'ont pas répondu ce round
    answered_player_ids = set(
        GameAnswer.objects.filter(round=round_obj).values_list("player_id", flat=True)
    )
    for gp in game.players.all():
        if gp.id not in answered_player_ids and gp.consecutive_correct > 0:
            gp.consecutive_correct = 0
            gp.save(update_fields=["consecutive_correct"])

    round_data = _serialize_to_dict(GameRoundSerializer(round_obj))
    _group_send(
        room_code,
        {
            "type": "broadcast_round_end",
            "results": {
                "correct_answer": round_obj.correct_answer,
                "round_data": round_data,
                "player_scores": _build_player_scores(round_obj),
                "updated_players": _build_updated_players(game),
            },
        },
    )


def broadcast_next_round(room_code: str, round_obj: GameRound, game: Game) -> None:
    """Broadcast that the game has moved to the next round."""
    from django.utils import timezone

    from apps.shop.models import BonusType, GameBonus

    round_data = _serialize_to_dict(GameRoundSerializer(round_obj))

    # Vérifier si un brouillard est actif pour ce round et l'injecter dans les données
    fog_bonus = (
        GameBonus.objects.filter(
            game=game,
            bonus_type=BonusType.FOG,
            round_number=round_obj.round_number,
            is_used=False,
        )
        .select_related("player__user")
        .first()
    )
    if fog_bonus:
        round_data["fog_active"] = True
        round_data["fog_activator"] = fog_bonus.player.user.username
        fog_bonus.is_used = True
        fog_bonus.used_at = timezone.now()
        fog_bonus.save(update_fields=["is_used", "used_at"])

    _group_send(
        room_code,
        {
            "type": "broadcast_next_round",
            "round_data": round_data,
            "updated_players": _build_updated_players(game),
        },
    )


def broadcast_game_finish(room_code: str, game: Game) -> None:
    """Broadcast that the game has finished with final results."""
    _group_send(
        room_code,
        {
            "type": "broadcast_game_finish",
            "results": _serialize_to_dict(GameSerializer(game)),
        },
    )
