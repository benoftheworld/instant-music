"""
Serializers for games.
"""
from rest_framework import serializers
from .models import Game, GamePlayer, GameRound, GameAnswer


class GamePlayerSerializer(serializers.ModelSerializer):
    """Serializer for GamePlayer."""
    
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    
    class Meta:
        model = GamePlayer
        fields = ['id', 'user', 'username', 'avatar', 'score', 'rank', 'is_connected', 'joined_at']
        read_only_fields = ['id', 'score', 'rank', 'joined_at']


class GameSerializer(serializers.ModelSerializer):
    """Serializer for Game."""
    
    players = GamePlayerSerializer(many=True, read_only=True)
    host_username = serializers.CharField(source='host.username', read_only=True)
    player_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Game
        fields = [
            'id',
            'room_code',
            'host',
            'host_username',
            'mode',
            'status',
            'max_players',
            'playlist_id',
            'is_online',
            'players',
            'player_count',
            'created_at',
            'started_at',
            'finished_at',
        ]
        read_only_fields = ['id', 'room_code', 'created_at']
    
    def get_player_count(self, obj):
        """Get number of players in the game."""
        return obj.players.count()


class CreateGameSerializer(serializers.ModelSerializer):
    """Serializer for creating a game."""
    
    class Meta:
        model = Game
        fields = ['mode', 'max_players', 'playlist_id', 'is_online']


class GameRoundSerializer(serializers.ModelSerializer):
    """Serializer for GameRound (hides correct answer during play)."""
    
    class Meta:
        model = GameRound
        fields = [
            'id',
            'game',
            'round_number',
            'track_id',
            'track_name',
            'artist_name',
            'options',
            'duration',
            'started_at',
            'ended_at',
        ]
        read_only_fields = ['id', 'started_at']


class GameRoundResultSerializer(serializers.ModelSerializer):
    """Serializer for GameRound with correct answer revealed."""
    
    class Meta:
        model = GameRound
        fields = [
            'id',
            'game',
            'round_number',
            'track_id',
            'track_name',
            'artist_name',
            'correct_answer',
            'options',
            'duration',
            'started_at',
            'ended_at',
        ]
        read_only_fields = ['id', 'started_at']


class GameAnswerSerializer(serializers.ModelSerializer):
    """Serializer for GameAnswer."""
    
    class Meta:
        model = GameAnswer
        fields = [
            'id',
            'round',
            'player',
            'answer',
            'is_correct',
            'points_earned',
            'response_time',
            'answered_at',
        ]
        read_only_fields = ['id', 'is_correct', 'points_earned', 'answered_at']
