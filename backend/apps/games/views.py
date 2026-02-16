"""
Views for games.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
import random
import string

from .models import Game, GamePlayer, GameAnswer
from .serializers import (
    GameSerializer,
    CreateGameSerializer,
    GamePlayerSerializer,
    GameRoundSerializer,
    GameAnswerSerializer,
    GameHistorySerializer,
    LeaderboardSerializer,
)
from .services import game_service


def generate_room_code() -> str:
    """Generate a unique 6-character room code."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Game.objects.filter(room_code=code).exists():
            return code


class GameViewSet(viewsets.ModelViewSet):
    """ViewSet for Game model."""
    
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'room_code'
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return CreateGameSerializer
        return GameSerializer
    
    def create(self, request):
        """Create a new game."""
        serializer = CreateGameSerializer(data=request.data)
        
        if serializer.is_valid():
            game = serializer.save(
                host=request.user,
                room_code=generate_room_code()
            )
            
            # Add host as a player
            GamePlayer.objects.create(
                game=game,
                user=request.user
            )
            
            return Response(
                GameSerializer(game).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def join(self, request, room_code=None):
        """Join a game."""
        game = self.get_object()
        
        # Check if game is joinable
        if game.status != 'waiting':
            return Response(
                {'error': 'La partie a déjà commencé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if game is full
        if game.players.count() >= game.max_players:
            return Response(
                {'error': 'La partie est pleine.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is already in the game
        if GamePlayer.objects.filter(game=game, user=request.user).exists():
            return Response(
                {'error': 'Vous êtes déjà dans cette partie.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add player to game
        player = GamePlayer.objects.create(
            game=game,
            user=request.user
        )
        
        # Notify all players via WebSocket
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        
        channel_layer = get_channel_layer()
        room_group_name = f'game_{room_code}'
        
        # Get updated game data
        game.refresh_from_db()
        game_serializer = GameSerializer(game, context={'request': request})
        player_serializer = GamePlayerSerializer(player, context={'request': request})
        
        # Broadcast player join to all clients in the room
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'broadcast_player_join',
                'player': player_serializer.data,
                'game_data': game_serializer.data
            }
        )
        
        return Response(
            player_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def start(self, request, room_code=None):
        """Start a game and generate rounds."""
        game = self.get_object()
        
        # Check if user is the host
        if game.host != request.user:
            return Response(
                {'error': 'Seul l\'hôte peut démarrer la partie.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if there are enough players
        if game.players.count() < 2:
            return Response(
                {'error': 'Au moins 2 joueurs sont nécessaires.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if playlist is selected
        if not game.playlist_id:
            return Response(
                {'error': 'Veuillez sélectionner une playlist.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Start game and generate rounds using service
            game, rounds = game_service.start_game(game)
            
            # Broadcast first round to all players via WebSocket
            if rounds:
                from asgiref.sync import async_to_sync
                from channels.layers import get_channel_layer
                from rest_framework.renderers import JSONRenderer
                import json
                
                channel_layer = get_channel_layer()
                room_group_name = f'game_{room_code}'
                first_round = rounds[0]
                
                # Serialize and convert to JSON-safe dict
                round_serializer = GameRoundSerializer(first_round)
                round_json = JSONRenderer().render(round_serializer.data)
                round_data = json.loads(round_json)
                
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        'type': 'broadcast_round_start',
                        'round_data': round_data
                    }
                )
            
            return Response({
                'game': GameSerializer(game).data,
                'rounds_created': len(rounds),
                'first_round': GameRoundSerializer(rounds[0]).data if rounds else None
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to start game {room_code}: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error starting game {room_code}: {e}")
            return Response(
                {'error': f'Erreur inattendue: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], url_path='current-round')
    def current_round(self, request, room_code=None):
        """Get the current round of the game."""
        game = self.get_object()
        
        # Check if player is in the game
        if not GamePlayer.objects.filter(game=game, user=request.user).exists():
            return Response(
                {'error': 'Vous n\'êtes pas dans cette partie.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        round_obj = game_service.get_current_round(game)
        
        if not round_obj:
            # Check for next round
            next_round = game_service.get_next_round(game)
            if next_round:
                return Response({
                    'current_round': None,
                    'next_round': GameRoundSerializer(next_round).data
                })
            else:
                return Response({
                    'current_round': None,
                    'message': 'Partie terminée'
                })
        
        # Don't send correct answer yet
        round_data = GameRoundSerializer(round_obj).data
        
        return Response({
            'current_round': round_data
        })
    
    @action(detail=True, methods=['post'])
    def answer(self, request, room_code=None):
        """Submit an answer for the current round."""
        game = self.get_object()
        
        # Get player
        try:
            player = GamePlayer.objects.get(game=game, user=request.user)
        except GamePlayer.DoesNotExist:
            return Response(
                {'error': 'Vous n\'êtes pas dans cette partie.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get current round
        round_obj = game_service.get_current_round(game)
        
        if not round_obj:
            return Response(
                {'error': 'Aucun round actif.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if player already answered
        if GameAnswer.objects.filter(round=round_obj, player=player).exists():
            return Response(
                {'error': 'Vous avez déjà répondu à ce round.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get answer and response time from request
        answer_text = request.data.get('answer')
        response_time = request.data.get('response_time', 0)
        
        if not answer_text:
            return Response(
                {'error': 'Aucune réponse fournie.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Submit answer using service
            game_answer = game_service.submit_answer(
                player=player,
                round_obj=round_obj,
                answer=answer_text,
                response_time=float(response_time)
            )
            
            # Check if all players have answered
            total_players = game.players.count()
            answered_players = GameAnswer.objects.filter(round=round_obj).count()
            
            # If all players answered, auto-end the round after short delay
            if answered_players >= total_players:
                from asgiref.sync import async_to_sync
                from channels.layers import get_channel_layer
                from rest_framework.renderers import JSONRenderer
                import json
                from django.utils import timezone
                
                # Mark round as ended
                round_obj.ended_at = timezone.now()
                round_obj.save()
                
                # Prepare results
                round_serializer = GameRoundSerializer(round_obj)
                round_json = JSONRenderer().render(round_serializer.data)
                round_data = json.loads(round_json)
                
                channel_layer = get_channel_layer()
                room_group_name = f'game_{room_code}'
                
                # Broadcast round end with correct answer
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        'type': 'broadcast_round_end',
                        'results': {
                            'correct_answer': round_obj.correct_answer,
                            'round_data': round_data
                        }
                    }
                )
            
            return Response(
                GameAnswerSerializer(game_answer).data,
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], url_path='next-round')
    def next_round(self, request, room_code=None):
        """Move to the next round (host only)."""
        game = self.get_object()
        
        # Check if user is the host
        if game.host != request.user:
            return Response(
                {'error': 'Seul l\'hôte peut passer au round suivant.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # End current round
        current = game_service.get_current_round(game)
        if current:
            game_service.end_round(current)
        
        # Get next round
        next_round = game_service.get_next_round(game)
        
        if not next_round:
            # No more rounds, finish game
            game = game_service.finish_game(game)
            
            # Broadcast game finished via WebSocket
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            
            channel_layer = get_channel_layer()
            room_group_name = f'game_{room_code}'
            
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'broadcast_game_finish',
                    'results': GameSerializer(game).data
                }
            )
            
            return Response({
                'game': GameSerializer(game).data,
                'message': 'Partie terminée'
            })
        
        # Broadcast next round via WebSocket
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        from rest_framework.renderers import JSONRenderer
        import json
        
        channel_layer = get_channel_layer()
        room_group_name = f'game_{room_code}'
        
        # Serialize and convert to JSON-safe dict
        round_serializer = GameRoundSerializer(next_round)
        round_json = JSONRenderer().render(round_serializer.data)
        round_data = json.loads(round_json)
        
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'broadcast_next_round',
                'round_data': round_data
            }
        )
        
        return Response(GameRoundSerializer(next_round).data)
    
    @action(detail=True, methods=['get'])
    def results(self, request, room_code=None):
        """Get final results and rankings."""
        game = self.get_object()
        
        # Check if player is in the game
        if not GamePlayer.objects.filter(game=game, user=request.user).exists():
            return Response(
                {'error': 'Vous n\'êtes pas dans cette partie.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get players ordered by score
        players = game.players.order_by('-score')
        
        return Response({
            'game': GameSerializer(game).data,
            'rankings': GamePlayerSerializer(players, many=True).data
        })
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get list of available games to join."""
        games = Game.objects.filter(
            status='waiting',
            is_online=True
        )
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get game history (finished games)."""
        # Get query params for pagination
        limit = request.query_params.get('limit', None)
        
        # Get finished games ordered by finished date
        games = Game.objects.filter(
            status='finished'
        ).select_related('host').prefetch_related('players__user').order_by('-finished_at')
        
        if limit:
            try:
                games = games[:int(limit)]
            except ValueError:
                pass
        
        serializer = GameHistorySerializer(games, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get global leaderboard of top players."""
        from apps.users.models import User
        
        # Get query params
        limit = request.query_params.get('limit', 10)
        
        try:
            limit = int(limit)
        except ValueError:
            limit = 10
        
        # Calculate stats for each user who played games
        leaderboard_data = []
        users = User.objects.filter(
            game_participations__isnull=False
        ).distinct()
        
        for user in users:
            # Get all game participations
            participations = GamePlayer.objects.filter(
                user=user,
                game__status='finished'
            )
            
            total_games = participations.count()
            if total_games == 0:
                continue
            
            total_points = participations.aggregate(
                total=Sum('score')
            )['total'] or 0
            
            # Count wins (rank = 1)
            total_wins = participations.filter(rank=1).count()
            
            win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
            
            leaderboard_data.append({
                'user_id': user.id,
                'username': user.username,
                'avatar': user.avatar.url if user.avatar else None,
                'total_games': total_games,
                'total_wins': total_wins,
                'total_points': total_points,
                'win_rate': round(win_rate, 1)
            })
        
        # Sort by total points
        leaderboard_data.sort(key=lambda x: x['total_points'], reverse=True)
        
        # Limit results
        leaderboard_data = leaderboard_data[:limit]
        
        serializer = LeaderboardSerializer(leaderboard_data, many=True)
        return Response(serializer.data)
