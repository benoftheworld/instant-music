"""
Views for stats.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Avg, Max, Count, Q

from apps.games.models import GamePlayer, GameAnswer, Game, GameMode
from apps.achievements.models import Achievement, UserAchievement
from apps.users.models import User, Team, TeamMember
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


class LeaderboardView(APIView):
    """General leaderboard - top players by total points."""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        limit = min(int(request.query_params.get('limit', 50)), 100)
        
        # Get users ordered by total_points with their team info
        users = User.objects.filter(
            total_games_played__gt=0
        ).prefetch_related('team_memberships__team').order_by('-total_points')[:limit]
        
        leaderboard = []
        for rank, user in enumerate(users, 1):
            # Get user's primary team (first one)
            team_membership = user.team_memberships.first()
            team_name = team_membership.team.name if team_membership else None
            
            leaderboard.append({
                'rank': rank,
                'user_id': user.id,
                'username': user.username,
                'avatar': user.avatar.url if user.avatar else None,
                'total_points': user.total_points,
                'total_games': user.total_games_played,
                'total_wins': user.total_wins,
                'win_rate': round(user.win_rate, 1),
                'team_name': team_name,
            })
        
        return Response(leaderboard)


class LeaderboardByModeView(APIView):
    """Leaderboard by game mode."""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, mode):
        limit = min(int(request.query_params.get('limit', 50)), 100)
        
        # Validate mode
        valid_modes = [choice[0] for choice in GameMode.choices]
        if mode not in valid_modes:
            return Response({'error': 'Mode invalide.'}, status=400)
        
        # Aggregate scores by user for this mode
        user_stats = GamePlayer.objects.filter(
            game__mode=mode,
            game__status='finished'
        ).values('user').annotate(
            total_points=Sum('score'),
            total_games=Count('id'),
            total_wins=Count('id', filter=Q(rank=1))
        ).order_by('-total_points')[:limit]
        
        # Get user details with team memberships
        user_ids = [stat['user'] for stat in user_stats]
        users = {u.id: u for u in User.objects.filter(id__in=user_ids).prefetch_related('team_memberships__team')}
        
        leaderboard = []
        for rank, stat in enumerate(user_stats, 1):
            user = users.get(stat['user'])
            if not user:
                continue
            # Get user's team
            team_membership = user.team_memberships.first()
            team_name = team_membership.team.name if team_membership else None
            
            win_rate = (stat['total_wins'] / stat['total_games'] * 100) if stat['total_games'] > 0 else 0
            leaderboard.append({
                'rank': rank,
                'user_id': stat['user'],
                'username': user.username,
                'avatar': user.avatar.url if user.avatar else None,
                'total_points': stat['total_points'],
                'total_games': stat['total_games'],
                'total_wins': stat['total_wins'],
                'win_rate': round(win_rate, 1),
                'team_name': team_name,
            })
        
        return Response(leaderboard)


class TeamLeaderboardView(APIView):
    """Team leaderboard - top teams by total points."""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        limit = min(int(request.query_params.get('limit', 50)), 100)
        
        # Get all teams ordered by total_points
        teams = Team.objects.all().order_by('-total_points', '-total_games')[:limit]
        
        leaderboard = []
        for rank, team in enumerate(teams, 1):
            leaderboard.append({
                'rank': rank,
                'team_id': team.id,
                'name': team.name,
                'avatar': team.avatar.url if team.avatar else None,
                'owner_name': team.owner.username if team.owner else None,
                'member_count': team.memberships.count(),
                'total_points': team.total_points,
                'total_games': team.total_games,
                'total_wins': team.total_wins,
                'win_rate': round((team.total_wins / team.total_games * 100) if team.total_games > 0 else 0, 1),
            })
        
        return Response(leaderboard)


class MyRankView(APIView):
    """Get current user's rank in the leaderboards."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # General rank
        general_rank = User.objects.filter(
            total_points__gt=user.total_points
        ).count() + 1
        
        total_players = User.objects.filter(total_games_played__gt=0).count()
        
        # Rank by mode
        mode_ranks = {}
        for mode_value, mode_label in GameMode.choices:
            user_points = GamePlayer.objects.filter(
                user=user,
                game__mode=mode_value,
                game__status='finished'
            ).aggregate(total=Sum('score'))['total'] or 0
            
            if user_points > 0:
                higher_ranked = GamePlayer.objects.filter(
                    game__mode=mode_value,
                    game__status='finished'
                ).values('user').annotate(
                    total=Sum('score')
                ).filter(total__gt=user_points).count()
                
                mode_ranks[mode_value] = {
                    'rank': higher_ranked + 1,
                    'points': user_points,
                    'label': mode_label
                }
        
        return Response({
            'general_rank': general_rank,
            'total_players': total_players,
            'mode_ranks': mode_ranks
        })
