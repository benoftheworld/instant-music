"""
Admin configuration for games.
"""
from django.contrib import admin
from .models import Game, GamePlayer, GameRound, GameAnswer


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Admin for Game model."""
    
    list_display = ['room_code', 'host', 'mode', 'status', 'player_count', 'created_at']
    list_filter = ['status', 'mode', 'is_online', 'created_at']
    search_fields = ['room_code', 'host__username']
    readonly_fields = ['room_code', 'created_at', 'started_at', 'finished_at']
    
    def player_count(self, obj):
        return obj.players.count()
    player_count.short_description = 'Players'


@admin.register(GamePlayer)
class GamePlayerAdmin(admin.ModelAdmin):
    """Admin for GamePlayer model."""
    
    list_display = ['user', 'game', 'score', 'rank', 'is_connected']
    list_filter = ['is_connected', 'joined_at']
    search_fields = ['user__username', 'game__room_code']


@admin.register(GameRound)
class GameRoundAdmin(admin.ModelAdmin):
    """Admin for GameRound model."""
    
    list_display = ['game', 'round_number', 'track_name', 'artist_name']
    list_filter = ['started_at']
    search_fields = ['game__room_code', 'track_name', 'artist_name']


@admin.register(GameAnswer)
class GameAnswerAdmin(admin.ModelAdmin):
    """Admin for GameAnswer model."""
    
    list_display = ['player', 'round', 'is_correct', 'points_earned', 'response_time']
    list_filter = ['is_correct', 'answered_at']
    search_fields = ['player__user__username']
