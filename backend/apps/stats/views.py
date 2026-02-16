"""
Views for stats.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Avg, Max, Count, Q

from apps.games.models import GamePlayer, GameAnswer
from apps.achievements.models import Achievement, UserAchievement
from .serializers import UserDetailedStatsSerializer


class UserDetailedStatsView(APIView):
    """Get detailed statistics for the current user."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Game stats from GamePlayer records
        game_players = GamePlayer.objects.filter(user=user, rank__isnull=False)
        total_games = game_players.count()
        total_wins = game_players.filter(rank=1).count()
        total_points = game_players.aggregate(s=Sum('score'))['s'] or 0
        best_score = game_players.aggregate(m=Max('score'))['m'] or 0
        avg_score = game_players.aggregate(a=Avg('score'))['a'] or 0.0
        
        # Answer stats
        answers = GameAnswer.objects.filter(player__user=user)
        total_answers = answers.count()
        total_correct = answers.filter(is_correct=True).count()
        accuracy = (total_correct / total_answers * 100) if total_answers > 0 else 0.0
        avg_response_time = answers.aggregate(a=Avg('response_time'))['a'] or 0.0
        
        # Win rate
        win_rate = (total_wins / total_games * 100) if total_games > 0 else 0.0
        
        # Achievements
        achievements_total = Achievement.objects.count()
        achievements_unlocked = UserAchievement.objects.filter(user=user).count()
        
        data = {
            'total_games_played': total_games,
            'total_wins': total_wins,
            'total_points': total_points,
            'win_rate': round(win_rate, 1),
            'avg_score_per_game': round(avg_score, 1),
            'best_score': best_score,
            'total_correct_answers': total_correct,
            'total_answers': total_answers,
            'accuracy': round(accuracy, 1),
            'avg_response_time': round(avg_response_time, 2),
            'achievements_unlocked': achievements_unlocked,
            'achievements_total': achievements_total,
        }
        
        serializer = UserDetailedStatsSerializer(data)
        return Response(serializer.data)
