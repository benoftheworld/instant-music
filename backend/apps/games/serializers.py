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
            'name',
            'room_code',
            'host',
            'host_username',
            'mode',
            'modes',
            'status',
            'max_players',
            'num_rounds',
            'playlist_id',
            'is_online',
            'answer_mode',
            'round_duration',
            'time_between_rounds',
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
    
    modes = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False,
        allow_empty=True,
        allow_null=True,
        default=None
    )
    
    class Meta:
        model = Game
        fields = [
            'name', 'mode', 'modes', 'max_players', 'num_rounds',
            'playlist_id', 'is_online', 'answer_mode',
            'round_duration', 'time_between_rounds',
        ]
        
    def validate_round_duration(self, value):
        """Validate round duration is within bounds."""
        if value < 10 or value > 60:
            raise serializers.ValidationError(
                'La durée d\'un round doit être entre 10 et 60 secondes.'
            )
        return value
    
    def validate_time_between_rounds(self, value):
        """Validate time between rounds is within bounds."""
        if value < 3 or value > 30:
            raise serializers.ValidationError(
                'Le temps entre les rounds doit être entre 3 et 30 secondes.'
            )
        return value
    
    def validate(self, data):
        """Ensure modes is set to empty list if not provided."""
        if data.get('modes') is None:
            data['modes'] = []
        return data


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
            'preview_url',
            'question_type',
            'question_text',
            'extra_data',
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
            'preview_url',
            'question_type',
            'question_text',
            'extra_data',
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


class GameHistorySerializer(serializers.ModelSerializer):
    """Serializer for game history with full details."""
    
    winner = serializers.SerializerMethodField()
    winner_score = serializers.SerializerMethodField()
    player_count = serializers.SerializerMethodField()
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    host_username = serializers.CharField(source='host.username', read_only=True)
    participants = serializers.SerializerMethodField()
    
    class Meta:
        model = Game
        fields = [
            'id',
            'room_code',
            'host_username',
            'mode',
            'mode_display',
            'playlist_id',
            'winner',
            'winner_score',
            'player_count',
            'participants',
            'created_at',
            'started_at',
            'finished_at',
        ]
    
    def get_winner(self, obj):
        """Get the winner of the game."""
        top_player = obj.players.order_by('-score').first()
        if top_player:
            return {
                'id': top_player.user.id,
                'username': top_player.user.username,
                'avatar': top_player.user.avatar.url if top_player.user.avatar else None
            }
        return None
    
    def get_winner_score(self, obj):
        """Get the winner's score."""
        top_player = obj.players.order_by('-score').first()
        return top_player.score if top_player else 0
    
    def get_player_count(self, obj):
        """Get number of players in the game."""
        return obj.players.count()
    
    def get_participants(self, obj):
        """Get list of all participants with their rankings."""
        players = obj.players.order_by('-score')
        return [{
            'id': player.user.id,
            'username': player.user.username,
            'avatar': player.user.avatar.url if player.user.avatar else None,
            'score': player.score,
            'rank': idx + 1
        } for idx, player in enumerate(players)]


class LeaderboardSerializer(serializers.Serializer):
    """Serializer for leaderboard data."""
    
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    avatar = serializers.CharField(allow_null=True)
    total_games = serializers.IntegerField()
    total_wins = serializers.IntegerField()
    total_points = serializers.IntegerField()
    win_rate = serializers.FloatField()
