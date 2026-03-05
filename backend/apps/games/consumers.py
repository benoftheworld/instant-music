"""
WebSocket consumers for games.
"""

import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.core.prometheus_metrics import (
    WS_CONNECTIONS_ACTIVE,
    WS_CONNECTIONS_TOTAL,
    WS_MESSAGES_TOTAL,
)

logger = logging.getLogger("apps.games.consumer")

# ── Schéma de validation des messages WebSocket entrants ─────────────────────
# Chaque type de message définit ses champs obligatoires et optionnels.
WS_MESSAGE_SCHEMAS: dict[str, dict] = {
    "player_join": {"required": set(), "optional": {"player"}},
    "player_answer": {
        "required": set(),
        "optional": {"player", "answer", "response_time"},
    },
    "start_game": {"required": set(), "optional": set()},
    "start_round": {"required": set(), "optional": {"round_data"}},
    "end_round": {"required": set(), "optional": {"results"}},
    "next_round": {"required": set(), "optional": {"round_data"}},
    "finish_game": {"required": set(), "optional": {"results"}},
    "activate_bonus": {"required": {"bonus_type"}, "optional": set()},
}

# Taille maximale d'un message WebSocket (16 Ko)
MAX_WS_MESSAGE_SIZE = 16 * 1024


def validate_ws_message(data: dict) -> str | None:
    """Valide un message WS entrant. Retourne un message d'erreur ou None."""
    msg_type = data.get("type")
    if not isinstance(msg_type, str):
        return "Le champ 'type' est requis et doit être une chaîne."

    schema = WS_MESSAGE_SCHEMAS.get(msg_type)
    if schema is None:
        return f"Type de message inconnu : {msg_type}"

    missing = schema["required"] - set(data.keys())
    if missing:
        return f"Champs requis manquants : {', '.join(sorted(missing))}"

    return None


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for user-specific notifications (invitations, etc.)."""

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user_id = user.id
        self.group_name = f"notifications_{self.user_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        logger.info(
            "notif_ws_connect",
            extra={"event_type": "connect", "user_id": self.user_id},
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # ── Broadcast handlers ────────────────────────────────────────────────────

    async def notify_game_invitation(self, event):
        """Push a game invitation notification to the connected user."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "game_invitation",
                    "invitation": event["invitation"],
                }
            )
        )

    async def notify_invitation_cancelled(self, event):
        """Notify the recipient that an invitation was cancelled."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "invitation_cancelled",
                    "invitation_id": event["invitation_id"],
                }
            )
        )

    async def notify_achievement_unlocked(self, event):
        """Push an achievement-unlocked notification to the connected user."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "achievement_unlocked",
                    "achievement": event["achievement"],
                }
            )
        )


class GameConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for game rooms."""

    async def connect(self):
        """Handle WebSocket connection."""
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]
        self.room_group_name = f"game_{self.room_code}"
        # scope["user"] est garanti authentifié par JwtWebSocketMiddleware
        user = self.scope["user"]

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # Métriques Prometheus
        WS_CONNECTIONS_TOTAL.labels(action="connect").inc()
        WS_CONNECTIONS_ACTIVE.inc()

        logger.info(
            "ws_connect",
            extra={
                "event_type": "connect",
                "room_code": self.room_code,
                "user_id": user.id,
            },
        )

        # Send connection confirmation
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "message": "Connected to game room",
                }
            )
        )

        await self._set_player_connected(True)
        game_data = await self.get_game_data()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_player_join",
                "player": {"user": str(user.id), "username": user.username},
                "game_data": game_data,
            },
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Métriques Prometheus
        WS_CONNECTIONS_TOTAL.labels(action="disconnect").inc()
        WS_CONNECTIONS_ACTIVE.dec()

        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        user = self.scope.get("user")
        if user and user.is_authenticated:
            logger.info(
                "ws_disconnect",
                extra={
                    "event_type": "disconnect",
                    "room_code": self.room_code,
                    "user_id": user.id,
                    "close_code": close_code,
                },
            )
            await self._set_player_connected(False)
            # Broadcast player leave with updated game data
            game_data = await self.get_game_data()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_player_leave",
                    "player": {
                        "user": str(user.id),
                        "username": user.username,
                    },
                    "game_data": game_data,
                },
            )

    async def receive(self, text_data):
        """Receive message from WebSocket."""
        # Limite de taille du message
        if len(text_data) > MAX_WS_MESSAGE_SIZE:
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "message": "Message trop volumineux."}
                )
            )
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            logger.warning(
                "ws_receive_error",
                extra={
                    "event_type": "error",
                    "room_code": self.room_code,
                    "error": "invalid_json",
                    "user_id": getattr(self.scope.get("user"), "id", None),
                },
            )
            await self.send(
                text_data=json.dumps({"type": "error", "message": "JSON invalide."})
            )
            return

        # Validation du schéma du message
        validation_error = validate_ws_message(data)
        if validation_error:
            await self.send(
                text_data=json.dumps({"type": "error", "message": validation_error})
            )
            return

        message_type = data["type"]

        # Métrique : message entrant
        WS_MESSAGES_TOTAL.labels(direction="inbound", message_type=message_type).inc()

        logger.debug(
            "ws_message",
            extra={
                "event_type": message_type,
                "room_code": self.room_code,
                "user_id": self.scope["user"].id,
            },
        )

        # Route message to appropriate handler
        handlers = {
            "player_join": self.player_join,
            "player_answer": self.player_answer,
            "start_game": self.start_game,
            "start_round": self.start_round,
            "end_round": self.end_round,
            "next_round": self.next_round,
            "finish_game": self.finish_game,
            "activate_bonus": self.activate_bonus,
        }

        handler = handlers.get(message_type)
        try:
            await handler(data)  # type: ignore[misc]
        except Exception:
            logger.exception(
                "ws_handler_error",
                extra={
                    "event_type": message_type,
                    "room_code": self.room_code,
                    "user_id": self.scope["user"].id,
                },
            )
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "error",
                        "message": "Erreur interne du serveur.",
                    }
                )
            )

    async def player_join(self, data):
        """Handle player joining the game (legacy WS message - prefer API call)."""
        # Get updated game data
        game_data = await self.get_game_data()

        # Broadcast to room group with updated player list
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_player_join",
                "player": data.get("player"),
                "game_data": game_data,
            },
        )

    @database_sync_to_async
    def get_game_data(self):
        """Get game data with players."""
        from django.conf import settings

        from .models import Game

        try:
            game = Game.objects.get(room_code=self.room_code)

            # Build absolute base URL from settings
            base_url = getattr(settings, "BACKEND_BASE_URL", "").rstrip("/")

            # Build game data manually to include proper avatar URLs
            players_data = []
            for player in game.players.select_related("user").all():
                avatar_url = None
                if player.user.avatar:
                    avatar_url = f"{base_url}{player.user.avatar.url}"

                players_data.append(
                    {
                        "id": str(player.id),
                        "user": str(player.user.id),
                        "username": player.user.username,
                        "avatar": avatar_url,
                        "score": player.score,
                        "rank": player.rank,
                        "is_connected": player.is_connected,
                        "joined_at": player.joined_at.isoformat(),
                    }
                )

            game_data = {
                "id": str(game.id),
                "room_code": game.room_code,
                "host": str(game.host.id),
                "host_username": game.host.username,
                "mode": game.mode,
                "status": game.status,
                "max_players": game.max_players,
                "playlist_id": game.playlist_id,
                "is_online": game.is_online,
                "answer_mode": game.answer_mode,
                "guess_target": game.guess_target,
                "round_duration": game.round_duration,
                "timer_start_round": game.timer_start_round,
                "score_display_duration": game.score_display_duration,
                "players": players_data,
                "player_count": len(players_data),
                "created_at": game.created_at.isoformat(),
                "started_at": (
                    game.started_at.isoformat() if game.started_at else None
                ),
                "finished_at": (
                    game.finished_at.isoformat() if game.finished_at else None
                ),
            }

            return game_data
        except Game.DoesNotExist:
            return None

    @database_sync_to_async
    def _set_player_connected(self, connected: bool):
        """Set the GamePlayer.is_connected flag for the current user in this room."""
        from .models import Game, GamePlayer

        try:
            game = Game.objects.get(room_code=self.room_code)
        except Game.DoesNotExist:
            return

        user = self.scope["user"]
        try:
            gp = GamePlayer.objects.get(game=game, user=user)
            gp.is_connected = connected
            gp.save(update_fields=["is_connected"])
        except GamePlayer.DoesNotExist:
            # No participation record: ignore
            return

    @database_sync_to_async
    def _is_host(self) -> bool:
        """Vérifie si l'utilisateur connecté est l'hôte de la partie."""
        from .models import Game

        return Game.objects.filter(  # type: ignore[no-any-return]
            room_code=self.room_code, host=self.scope["user"]
        ).exists()

    async def player_answer(self, data):
        """Handle player submitting an answer."""
        player_username = data.get("player")
        answer = data.get("answer")
        response_time = data.get("response_time", 0)

        # Broadcast that player answered (without revealing correctness yet)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_player_answer",
                "player": player_username,
                "answered": True,
            },
        )

    async def start_game(self, data):
        """Handle game start."""
        if not await self._is_host():
            logger.warning(
                "ws_auth_forbidden",
                extra={
                    "action": "start_game",
                    "user_id": self.scope["user"].id,
                    "room_code": self.room_code,
                },
            )
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "message": "Action réservée à l'hôte."}
                )
            )
            return

        # Get initial game data
        game_data = await self.get_game_data()

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "broadcast_game_start", "game_data": game_data},
        )

    async def start_round(self, data):
        """Handle round start."""
        if not await self._is_host():
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "message": "Action réservée à l'hôte."}
                )
            )
            return

        round_data = data.get("round_data")

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "broadcast_round_start", "round_data": round_data},
        )

    async def end_round(self, data):
        """Handle round end."""
        if not await self._is_host():
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "message": "Action réservée à l'hôte."}
                )
            )
            return

        round_results = data.get("results")

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "broadcast_round_end", "results": round_results},
        )

    async def next_round(self, data):
        """Handle next round."""
        if not await self._is_host():
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "message": "Action réservée à l'hôte."}
                )
            )
            return

        round_data = data.get("round_data")

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "broadcast_next_round", "round_data": round_data},
        )

    async def activate_bonus(self, data):
        """Handle bonus activation from a player during a game."""
        user = self.scope["user"]
        bonus_type = data.get("bonus_type")

        if not bonus_type:
            await self.send(
                text_data=json.dumps({"type": "error", "message": "bonus_type requis."})
            )
            return

        result = await self._do_activate_bonus(user, bonus_type)

        if result.get("error"):
            await self.send(
                text_data=json.dumps({"type": "error", "message": result["error"]})
            )
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_bonus_activated",
                "bonus": {
                    "bonus_type": bonus_type,
                    "username": user.username,
                    "round_number": result.get("round_number"),
                },
            },
        )

    @database_sync_to_async
    def _do_activate_bonus(self, user, bonus_type: str) -> dict:
        """Synchronous DB calls for bonus activation."""
        from apps.shop.services import (
            BonusAlreadyActiveError,
            ItemNotAvailableError,
            bonus_service,
        )

        from .models import Game

        try:
            game = Game.objects.get(room_code=self.room_code)
        except Game.DoesNotExist:
            return {"error": "Partie introuvable."}

        current_round = game.rounds.filter(
            started_at__isnull=False, ended_at__isnull=True
        ).first()
        round_number = current_round.round_number if current_round else None

        try:
            game_bonus = bonus_service.activate_bonus(
                user, game, bonus_type, round_number=round_number
            )
            return {"round_number": game_bonus.round_number}
        except (ItemNotAvailableError, ValueError) as e:
            return {"error": str(e)}
        except BonusAlreadyActiveError as e:
            return {"error": str(e)}

    async def finish_game(self, data):
        """Handle game finish."""
        if not await self._is_host():
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "message": "Action réservée à l'hôte."}
                )
            )
            return

        results = data.get("results")

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "broadcast_game_finish", "results": results},
        )

    # Broadcast handlers
    async def broadcast_player_join(self, event):
        """Send player join notification to WebSocket."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "player_joined",
                    "player": event["player"],
                    "game_data": event.get("game_data"),
                }
            )
        )

    async def broadcast_player_leave(self, event):
        """Send player leave notification to WebSocket."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "player_leave",
                    "player": event.get("player"),
                    "game_data": event.get("game_data"),
                }
            )
        )

    async def broadcast_game_update(self, event):
        """Send general game state update to WebSocket."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "game_updated",
                    "game_data": event.get("game_data"),
                }
            )
        )

    async def broadcast_player_answer(self, event):
        """Send player answer notification to WebSocket."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "player_answered",
                    "player": event["player"],
                    "answered": event.get("answered", True),
                }
            )
        )

    async def broadcast_game_start(self, event):
        """Send game start to WebSocket."""
        try:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "game_started",
                        "game_data": event.get("game_data"),
                    }
                )
            )
        except RuntimeError:
            # Connection already closed (client navigated away during start)
            pass

    async def broadcast_round_start(self, event):
        """Send round start to WebSocket."""
        await self.send(
            text_data=json.dumps(
                {"type": "round_started", "round_data": event["round_data"]}
            )
        )

    async def broadcast_round_end(self, event):
        """Send round end with results to WebSocket."""
        await self.send(
            text_data=json.dumps({"type": "round_ended", "results": event["results"]})
        )

    async def broadcast_next_round(self, event):
        """Send next round data to WebSocket."""
        message = {
            "type": "next_round",
            "round_data": event["round_data"],
        }
        if "updated_players" in event:
            message["updated_players"] = event["updated_players"]
        await self.send(text_data=json.dumps(message))

    async def broadcast_game_finish(self, event):
        """Send game finish with final results to WebSocket."""
        await self.send(
            text_data=json.dumps({"type": "game_finished", "results": event["results"]})
        )

    async def broadcast_bonus_activated(self, event):
        """Broadcast to all players that a bonus has been activated."""
        payload: dict = {
            "type": "bonus_activated",
            "bonus": event["bonus"],
        }
        if "new_duration" in event:
            payload["new_duration"] = event["new_duration"]
        if "updated_players" in event:
            payload["updated_players"] = event["updated_players"]
        await self.send(text_data=json.dumps(payload))
