"""
Views for games.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
import random
import string

from .models import Game, GamePlayer, GameRound, GameAnswer
from .serializers import (
    GameSerializer,
    CreateGameSerializer,
    GamePlayerSerializer,
    GameRoundSerializer,
    GameAnswerSerializer,
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
        
        return Response(
            GamePlayerSerializer(player).data,
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
            
            return Response({
                'game': GameSerializer(game).data,
                'rounds_created': len(rounds),
                'first_round': GameRoundSerializer(rounds[0]).data if rounds else None
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
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
        
        return Response(round_data)
    
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
            return Response({
                'game': GameSerializer(game).data,
                'message': 'Partie terminée'
            })
        
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
