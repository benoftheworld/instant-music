"""
Broadcast service for sending real-time game updates via Django Channels.

Centralises WebSocket broadcast logic previously duplicated across
GameViewSet actions (answer, end_current_round, next_round, start).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.renderers import JSONRenderer

from .models import Game, GameAnswer, GameRound
from .serializers import GameRoundSerializer, GameSerializer

logger = logging.getLogger(__name__)


def _serialize_to_dict(serializer) -> dict:
    """Render a DRF serializer to a plain JSON-safe dict."""
    raw = JSONRenderer().render(serializer.data)
    return json.loads(raw)


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
        }
    return scores


def _build_updated_players(game: Game) -> list[dict[str, Any]]:
    """Build ordered list of players with current totals."""
    return [
        {
            "id": p.id,
            "user": p.user.id,
            "username": p.user.username,
            "score": p.score,
            "rank": p.rank,
            "is_connected": p.is_connected,
            "avatar": p.user.avatar.url if p.user.avatar else None,
        }
        for p in game.players.select_related("user").order_by("-score")
    ]


def _group_name(room_code: str) -> str:
    return f"game_{room_code}"


# ── Public broadcast helpers ────────────────────────────────────────────


def broadcast_player_join(
    room_code: str, player_data: dict, game_data: dict
) -> None:
    """Notify all clients that a new player joined the room."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        _group_name(room_code),
        {
            "type": "broadcast_player_join",
            "player": player_data,
            "game_data": game_data,
        },
    )


def broadcast_player_leave(
    room_code: str, player_data: dict, game_data: dict
) -> None:
    """Notify all clients that a player left the room."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        _group_name(room_code),
        {
            "type": "broadcast_player_leave",
            "player": player_data,
            "game_data": game_data,
        },
    )


def broadcast_round_start(room_code: str, round_obj: GameRound) -> None:
    """Broadcast that a round has started with its data."""
    channel_layer = get_channel_layer()
    round_data = _serialize_to_dict(GameRoundSerializer(round_obj))
    async_to_sync(channel_layer.group_send)(
        _group_name(room_code),
        {
            "type": "broadcast_round_start",
            "round_data": round_data,
        },
    )


def broadcast_round_end(
    room_code: str, round_obj: GameRound, game: Game
) -> None:
    """Broadcast round end with correct answer, per-player scores, and updated totals."""
    channel_layer = get_channel_layer()
    round_data = _serialize_to_dict(GameRoundSerializer(round_obj))
    async_to_sync(channel_layer.group_send)(
        _group_name(room_code),
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


def broadcast_next_round(
    room_code: str, round_obj: GameRound, game: Game
) -> None:
    """Broadcast that the game has moved to the next round."""
    channel_layer = get_channel_layer()
    round_data = _serialize_to_dict(GameRoundSerializer(round_obj))
    async_to_sync(channel_layer.group_send)(
        _group_name(room_code),
        {
            "type": "broadcast_next_round",
            "round_data": round_data,
            "updated_players": _build_updated_players(game),
        },
    )


def broadcast_game_finish(room_code: str, game: Game) -> None:
    """Broadcast that the game has finished with final results."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        _group_name(room_code),
        {
            "type": "broadcast_game_finish",
            "results": GameSerializer(game).data,
        },
    )
