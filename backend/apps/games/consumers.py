"""WebSocket consumers for games.
"""

import json
import logging
import time

import redis.asyncio as aioredis
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.core.prometheus_metrics import (
    WS_CONNECTIONS_ACTIVE,
    WS_CONNECTIONS_TOTAL,
    WS_MESSAGES_TOTAL,
)

logger = logging.getLogger("apps.games.consumer")

# ── Rate limiting WebSocket (fenêtre glissante Redis) ────────────────────────
# Clé Redis : ws_rl:{user_id}:{room_code}:{message_type}
# Valeurs : (max_messages, window_seconds)
_WS_RATE_LIMITS: dict[str, tuple[int, int]] = {
    "player_answer": (5, 10),   # 5 réponses par 10 s (anti-spam de réponses)
    "activate_bonus": (3, 60),  # 3 activations de bonus par 60 s
    "player_join": (5, 30),     # 5 tentatives de join par 30 s
    "start_game": (3, 60),      # 3 tentatives par 60 s (action ponctuelle)
    "_default": (30, 10),       # filet de sécurité global
}

# Script Lua : fenêtre glissante atomique (scored set + pruning)
# KEYS[1] = clé du compteur
# ARGV[1] = timestamp courant (ms), ARGV[2] = largeur fenêtre (ms), ARGV[3] = limite
# Retourne 1 si la requête est autorisée, 0 si throttlée.
_SLIDING_WINDOW_SCRIPT = """
local key    = KEYS[1]
local now_ms = tonumber(ARGV[1])
local win_ms = tonumber(ARGV[2])
local limit  = tonumber(ARGV[3])
redis.call('ZREMRANGEBYSCORE', key, '-inf', now_ms - win_ms)
local count = redis.call('ZCARD', key)
if count >= limit then
    return 0
end
local seq = redis.call('INCR', key .. ':seq')
redis.call('ZADD', key, now_ms, now_ms .. ':' .. seq)
local ttl = math.ceil(win_ms / 1000) + 1
redis.call('EXPIRE', key, ttl)
redis.call('EXPIRE', key .. ':seq', ttl)
return 1
"""

_ws_redis_client: aioredis.Redis | None = None  # pool partagé par le process


def _get_ws_redis() -> aioredis.Redis:
    """Retourne (ou crée) le client Redis async dédié au rate limiting WS."""
    global _ws_redis_client
    if _ws_redis_client is None:
        from django.conf import settings

        url = settings.CACHES["default"]["LOCATION"]
        _ws_redis_client = aioredis.from_url(url, decode_responses=True)
    return _ws_redis_client


# ── Schéma de validation des messages WebSocket entrants ─────────────────────
# Chaque type de message définit ses champs obligatoires et optionnels.
WS_MESSAGE_SCHEMAS: dict[str, dict] = {
    "ping": {"required": set(), "optional": set()},
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

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming messages (heartbeat ping)."""
        if text_data:
            try:
                data = json.loads(text_data)
                if data.get("type") == "ping":
                    await self.send(text_data=json.dumps({"type": "pong"}))
            except (json.JSONDecodeError, TypeError):
                pass

    # ── Broadcast handlers ────────────────────────────────────────────────────

    # Dispatch map: channel-layer type → (ws message type, event data key)
    _NOTIFICATION_MAP: dict[str, tuple[str, str]] = {
        "notify_game_invitation": ("game_invitation", "invitation"),
        "notify_invitation_cancelled": ("invitation_cancelled", "invitation_id"),
        "notify_achievement_unlocked": ("achievement_unlocked", "achievement"),
        "notify_friend_request": ("friend_request", "friendship"),
        "notify_friend_request_accepted": ("friend_request_accepted", "friendship"),
        "notify_team_join_request": ("team_join_request", "request"),
        "notify_team_join_approved": ("team_join_approved", "approval"),
        "notify_team_join_rejected": ("team_join_rejected", "rejection"),
        "notify_team_role_updated": ("team_role_updated", "role_update"),
        "notify_team_member_kicked": ("team_member_kicked", "kick"),
    }

    def __getattr__(self, name: str):
        """Generic handler for all notification types defined in _NOTIFICATION_MAP."""
        entry = self._NOTIFICATION_MAP.get(name)
        if entry is None:
            raise AttributeError(name)
        msg_type, data_key = entry

        async def _handler(event):
            await self.send(
                text_data=json.dumps({"type": msg_type, data_key: event[data_key]})
            )

        return _handler


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

        # Heartbeat : répondre immédiatement sans rate-limiting ni routing
        if message_type == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))
            return

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

        # ── Rate limiting (fenêtre glissante Redis) ───────────────────────────
        if not await self._check_rate_limit(message_type):
            logger.warning(
                "ws_rate_limit",
                extra={
                    "event_type": "rate_limit",
                    "room_code": self.room_code,
                    "user_id": self.scope["user"].id,
                    "message_type": message_type,
                },
            )
            await self.send(
                text_data=json.dumps(
                    {"type": "error", "message": "Trop de messages. Veuillez patienter."}
                )
            )
            return

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

    async def _check_rate_limit(self, message_type: str) -> bool:
        """Vérifie la limite de débit via fenêtre glissante Redis.

        Retourne True si la requête est autorisée, False si throttlée.
        """
        user_id = self.scope["user"].id
        limit, window = _WS_RATE_LIMITS.get(message_type, _WS_RATE_LIMITS["_default"])
        key = f"ws_rl:{user_id}:{self.room_code}:{message_type}"
        now_ms = int(time.time() * 1000)
        win_ms = window * 1000
        try:
            result = await _get_ws_redis().eval(
                _SLIDING_WINDOW_SCRIPT, 1, key, now_ms, win_ms, limit
            )
            return bool(result)
        except Exception:
            # En cas d'erreur Redis, bloquer la requête (fail-closed) pour éviter
            # qu'un attaquant puisse contourner le rate limiting en provoquant
            # une indisponibilité Redis.
            logger.exception(
                "ws_rate_limit_redis_error",
                extra={"room_code": self.room_code, "user_id": user_id},
            )
            return False

    async def player_join(self, data):
        """Handle player joining the game (legacy WS message - prefer API call)."""
        # Get updated game data
        game_data = await self.get_game_data()

        # Broadcast to room group with updated player list
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_player_join",
                "player": {"user": str(self.scope["user"].id), "username": self.scope["user"].username},
                "game_data": game_data,
            },
        )

    @database_sync_to_async
    def get_game_data(self):
        """Get game data with players."""
        from django.conf import settings
        from django.db.models import Prefetch

        from .models import Game, GamePlayer

        try:
            game = (
                Game.objects.select_related("host")
                .prefetch_related(
                    Prefetch(
                        "players",
                        queryset=GamePlayer.objects.select_related("user"),
                    )
                )
                .get(room_code=self.room_code)
            )

            # Build absolute base URL from settings
            base_url = getattr(settings, "BACKEND_BASE_URL", "").rstrip("/")

            # Build game data manually to include proper avatar URLs
            players_data = []
            for player in game.players.all():
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
    async def _require_host(self, action: str) -> bool:
        """Vérifie que l'utilisateur est l'hôte. Envoie une erreur et log si non.

        Returns True si l'utilisateur est l'hôte, False sinon.
        """
        if await self._is_host():
            return True
        logger.warning(
            "ws_auth_forbidden",
            extra={
                "action": action,
                "user_id": self.scope["user"].id,
                "room_code": self.room_code,
            },
        )
        await self.send(
            text_data=json.dumps(
                {"type": "error", "message": "Action réservée à l'hôte."}
            )
        )
        return False
    @database_sync_to_async
    def _check_all_party_players_answered(self) -> bool:
        """En mode soirée : vérifie si tous les joueurs non-hôte ont soumis une réponse
        pour le round en cours. Retourne False si la partie n'est pas en mode soirée,
        si aucun round n'est actif, ou si aucun joueur non-hôte n'existe.

        Optimized: uses a single query with subquery instead of multiple counts.
        """
        from .models import Game, GameAnswer, GamePlayer

        try:
            game = Game.objects.select_related("host").get(room_code=self.room_code)
        except Game.DoesNotExist:
            return False

        if not game.is_party_mode:
            return False

        current_round = game.rounds.filter(
            started_at__isnull=False, ended_at__isnull=True
        ).first()
        if current_round is None:
            return False

        non_host_players = GamePlayer.objects.filter(game=game).exclude(
            user=game.host
        )
        non_host_count = non_host_players.count()
        if non_host_count == 0:
            return False

        answered_count = GameAnswer.objects.filter(
            round=current_round, player__in=non_host_players
        ).count()

        return answered_count >= non_host_count  # type: ignore[return-value]

    async def player_answer(self, data):
        """Handle player submitting an answer."""
        # On utilise l'identité authentifiée (scope) pour éviter l'usurpation.
        player_username = self.scope["user"].username

        # Broadcast that player answered (without revealing correctness yet)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_player_answer",
                "player": player_username,
                "answered": True,
            },
        )

        # En mode soirée, si tous les joueurs (hors présentateur) ont répondu,
        # déclencher immédiatement la fin du round sans attendre le timer.
        all_answered = await self._check_all_party_players_answered()
        if all_answered:
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "broadcast_all_answered"},
            )

    async def start_game(self, data):
        """Handle game start."""
        if not await self._require_host("start_game"):
            return

        # Get initial game data
        game_data = await self.get_game_data()

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "broadcast_game_start", "game_data": game_data},
        )

    async def start_round(self, data):
        """Handle round start."""
        if not await self._require_host("start_round"):
            return

        round_data = await self._enrich_round_data_with_fog(data.get("round_data") or {})

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "broadcast_round_start", "round_data": round_data},
        )

    async def end_round(self, data):
        """Handle round end."""
        if not await self._require_host("end_round"):
            return

        round_results = data.get("results")

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "broadcast_round_end", "results": round_results},
        )

    async def next_round(self, data):
        """Handle next round."""
        if not await self._require_host("next_round"):
            return

        round_data = await self._enrich_round_data_with_fog(data.get("round_data") or {})

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
            BonusActivationError,
            BonusAlreadyActiveError,
            ItemNotAvailableError,
            bonus_service,
        )

        from .models import Game

        try:
            game = Game.objects.get(room_code=self.room_code)
        except Game.DoesNotExist:
            return {"error": "Partie introuvable."}

        if not game.is_online:
            return {
                "error": "Les bonus sont désactivés en mode hors ligne (solo)."
            }

        try:
            round_number, _ = bonus_service.resolve_round_number(game, bonus_type)
        except BonusActivationError as e:
            return {"error": str(e)}

        try:
            game_bonus = bonus_service.activate_bonus(
                user, game, bonus_type, round_number=round_number
            )
            return {"round_number": game_bonus.round_number}
        except (ItemNotAvailableError, ValueError) as e:
            return {"error": str(e)}
        except BonusAlreadyActiveError as e:
            return {"error": str(e)}

    async def _enrich_round_data_with_fog(self, round_data: dict) -> dict:
        """Injecte les données de brouillard dans round_data si un bonus fog est actif."""
        round_number = round_data.get("round_number") if round_data else None
        if round_number is not None:
            fog_active, fog_activator = await self._check_and_consume_fog(round_number)
            if fog_active:
                round_data = dict(round_data)
                round_data["fog_active"] = True
                round_data["fog_activator"] = fog_activator
        return round_data

    @database_sync_to_async
    def _check_and_consume_fog(self, round_number: int) -> tuple[bool, str | None]:
        """Vérifie si un bonus brouillard est actif pour ce round, le consomme et
        retourne (fog_active, username_activateur).
        """
        from django.utils import timezone

        from apps.shop.models import BonusType, GameBonus

        bonus = (
            GameBonus.objects.filter(
                game__room_code=self.room_code,
                bonus_type=BonusType.FOG,
                round_number=round_number,
                is_used=False,
            )
            .select_related("player__user")
            .first()
        )
        if bonus:
            username = bonus.player.user.username
            bonus.is_used = True
            bonus.used_at = timezone.now()
            bonus.save(update_fields=["is_used", "used_at"])
            return True, username  # type: ignore[return-value]
        return False, None  # type: ignore[return-value]

    async def finish_game(self, data):
        """Handle game finish."""
        if not await self._require_host("finish_game"):
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

    async def broadcast_all_answered(self, event):
        """Notifie que tous les joueurs (hors présentateur) ont répondu — mode soirée."""
        await self.send(text_data=json.dumps({"type": "all_players_answered"}))

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
