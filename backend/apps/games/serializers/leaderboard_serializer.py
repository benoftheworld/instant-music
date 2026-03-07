"""Serializer for leaderboard data."""

from rest_framework import serializers


class LeaderboardSerializer(serializers.Serializer):
    """Serializer for leaderboard data."""

    user_id = serializers.IntegerField()
    username = serializers.CharField()
    avatar = serializers.CharField(allow_null=True)
    total_games = serializers.IntegerField()
    total_wins = serializers.IntegerField()
    total_points = serializers.IntegerField()
    win_rate = serializers.FloatField()
