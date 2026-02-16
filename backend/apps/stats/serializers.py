"""
Serializers for stats.
"""
from rest_framework import serializers


class UserDetailedStatsSerializer(serializers.Serializer):
    """Serializer for detailed user statistics."""
    
    total_games_played = serializers.IntegerField()
    total_wins = serializers.IntegerField()
    total_points = serializers.IntegerField()
    win_rate = serializers.FloatField()
    avg_score_per_game = serializers.FloatField()
    best_score = serializers.IntegerField()
    total_correct_answers = serializers.IntegerField()
    total_answers = serializers.IntegerField()
    accuracy = serializers.FloatField()
    avg_response_time = serializers.FloatField()
    achievements_unlocked = serializers.IntegerField()
    achievements_total = serializers.IntegerField()
