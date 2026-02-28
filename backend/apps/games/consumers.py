"""
WebSocket consumers for games.
"""

import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.core.prometheus_metrics import (
    WS_CONNECTIONS_TOTAL,
    WS_CONNECTIONS_ACTIVE,
    WS_MESSAGES_TOTAL,
)

logger = logging.getLogger("apps.games.consumer")


class GameConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for game rooms."""

    async def connect(self):
        """Handle WebSocket connection."""
        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]
        self.room_group_name = f"game_{self.room_code}"
        # scope["user"] est garanti authentifié par JwtWebSocketMiddleware
        user = self.scope["user"]

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )

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
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

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
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            # Métrique : message entrant
            WS_MESSAGES_TOTAL.labels(
                direction="inbound", message_type=message_type or "unknown"
            ).inc()

            logger.debug(
                "ws_message",
                extra={
                    "event_type": message_type,
                    "room_code": self.room_code,
                    "user_id": self.scope["user"].id,
                },
            )

            # Route message to appropriate handler
            if message_type == "player_join":
                await self.player_join(data)
            elif message_type == "player_answer":
                await self.player_answer(data)
            elif message_type == "start_game":
                await self.start_game(data)
            elif message_type == "start_round":
                await self.start_round(data)
            elif message_type == "end_round":
                await self.end_round(data)
            elif message_type == "next_round":
                await self.next_round(data)
            elif message_type == "finish_game":
                await self.finish_game(data)
            else:
                await self.send(
                    text_data=json.dumps(
                        {"type": "error", "message": "Unknown message type"}
                    )
                )

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
                text_data=json.dumps(
                    {"type": "error", "message": "Invalid JSON"}
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
        from .models import Game
        from django.conf import settings

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
        from .models import GamePlayer, Game

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

        return Game.objects.filter(
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
            text_data=json.dumps(
                {"type": "round_ended", "results": event["results"]}
            )
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
            text_data=json.dumps(
                {"type": "game_finished", "results": event["results"]}
            )
        )
