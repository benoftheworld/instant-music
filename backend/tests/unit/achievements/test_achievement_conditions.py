"""Tests unitaires des condition checkers du service achievements."""

from unittest.mock import MagicMock, patch

from tests.base import BaseServiceUnitTest


class TestCheckGamesPlayed(BaseServiceUnitTest):
    """Vérifie _check_games_played."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    def test_met_when_enough_games(self):
        from apps.achievements.services import _check_games_played
        user = MagicMock(total_games_played=10)
        assert _check_games_played(user, 5, None, None, None) is True

    def test_not_met_when_insufficient(self):
        from apps.achievements.services import _check_games_played
        user = MagicMock(total_games_played=3)
        assert _check_games_played(user, 5, None, None, None) is False


class TestCheckWins(BaseServiceUnitTest):
    """Vérifie _check_wins."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    def test_met(self):
        from apps.achievements.services import _check_wins
        user = MagicMock(total_wins=10)
        assert _check_wins(user, 5, None, None, None) is True

    def test_not_met(self):
        from apps.achievements.services import _check_wins
        user = MagicMock(total_wins=2)
        assert _check_wins(user, 5, None, None, None) is False


class TestCheckPoints(BaseServiceUnitTest):
    """Vérifie _check_points."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    def test_met(self):
        from apps.achievements.services import _check_points
        user = MagicMock(total_points=1000)
        assert _check_points(user, 500, None, None, None) is True

    def test_not_met(self):
        from apps.achievements.services import _check_points
        user = MagicMock(total_points=100)
        assert _check_points(user, 500, None, None, None) is False


class TestCheckPerfectRound(BaseServiceUnitTest):
    """Vérifie _check_perfect_round."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    def test_true_when_perfect_game(self):
        from apps.achievements.services import _check_perfect_round
        assert _check_perfect_round(MagicMock(), 0, None, None, {"perfect_game": True}) is True

    def test_false_when_no_round_data(self):
        from apps.achievements.services import _check_perfect_round
        assert _check_perfect_round(MagicMock(), 0, None, None, None) is False

    def test_false_when_not_perfect(self):
        from apps.achievements.services import _check_perfect_round
        assert _check_perfect_round(MagicMock(), 0, None, None, {"perfect_game": False}) is False


class TestCheckAllFastRound(BaseServiceUnitTest):
    """Vérifie _check_all_fast_round."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    def test_true_when_fast(self):
        from apps.achievements.services import _check_all_fast_round
        rd = {"perfect_game": True, "max_response_time": 1.5}
        assert _check_all_fast_round(MagicMock(), 0, "2.0", None, rd) is True

    def test_false_when_slow(self):
        from apps.achievements.services import _check_all_fast_round
        rd = {"perfect_game": True, "max_response_time": 3.0}
        assert _check_all_fast_round(MagicMock(), 0, "2.0", None, rd) is False

    def test_false_when_no_round_data(self):
        from apps.achievements.services import _check_all_fast_round
        assert _check_all_fast_round(MagicMock(), 0, None, None, None) is False


class TestCheckInGameStreak(BaseServiceUnitTest):
    """Vérifie _check_in_game_streak."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    def test_true_with_streak(self):
        from apps.achievements.services import _check_in_game_streak
        assert _check_in_game_streak(MagicMock(), 5, None, None, {"max_streak": 7}) is True

    def test_false_without_round_data(self):
        from apps.achievements.services import _check_in_game_streak
        assert _check_in_game_streak(MagicMock(), 5, None, None, None) is False


class TestCheckDominantWin(BaseServiceUnitTest):
    """Vérifie _check_dominant_win."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    def test_true(self):
        from apps.achievements.services import _check_dominant_win
        assert _check_dominant_win(MagicMock(), 0, None, None, {"dominant_win": True}) is True

    def test_false_no_data(self):
        from apps.achievements.services import _check_dominant_win
        assert _check_dominant_win(MagicMock(), 0, None, None, None) is False


class TestCheckGlobalStreak(BaseServiceUnitTest):
    """Vérifie _check_global_streak."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    def test_true_from_round_data(self):
        from apps.achievements.services import _check_global_streak
        assert _check_global_streak(MagicMock(), 5, None, None, {"max_streak": 10}) is True

    def test_false_from_round_data(self):
        from apps.achievements.services import _check_global_streak
        assert _check_global_streak(MagicMock(), 5, None, None, {"max_streak": 2}) is False


class TestPushAchievementNotification(BaseServiceUnitTest):
    """Vérifie _push_achievement_notification."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    @patch("apps.achievements.services.get_channel_layer")
    @patch("apps.achievements.services.async_to_sync")
    def test_sends_notification(self, mock_a2s, mock_get_cl):
        from apps.achievements.services import _push_achievement_notification

        mock_ach = MagicMock()
        mock_ach.id = "ach1"
        mock_ach.name = "Pro"
        mock_ach.description = "Desc"
        mock_ach.icon = None
        mock_ach.points = 10

        mock_send = MagicMock()
        mock_a2s.return_value = mock_send

        _push_achievement_notification(42, mock_ach)
        mock_send.assert_called_once()

    @patch("apps.achievements.services.get_channel_layer", return_value=None)
    def test_no_channel_layer(self, mock_get_cl):
        from apps.achievements.services import _push_achievement_notification

        mock_ach = MagicMock()
        # Should not raise
        _push_achievement_notification(42, mock_ach)


class TestCheckCondition(BaseServiceUnitTest):
    """Vérifie _check_condition dispatcher."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    def test_unknown_condition_type(self):
        from apps.achievements.services import AchievementService

        svc = AchievementService()
        ach = MagicMock()
        ach.condition_type = "unknown_type"
        ach.condition_value = 0
        ach.condition_extra = None
        assert svc._check_condition(MagicMock(), ach) is False


class TestCheckWinStreak(BaseServiceUnitTest):
    """Vérifie _check_win_streak."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    @patch("apps.games.models.GamePlayer")
    def test_streak_met(self, mock_gp):
        from apps.achievements.services import _check_win_streak

        qs = MagicMock()
        mock_gp.objects.filter.return_value.order_by.return_value.__getitem__ = lambda s, k: qs
        qs.count.return_value = 3
        p1 = MagicMock(rank=1)
        p2 = MagicMock(rank=1)
        p3 = MagicMock(rank=1)
        qs.__iter__ = lambda s: iter([p1, p2, p3])
        result = _check_win_streak(MagicMock(), 3, None, None, None)
        assert result is True

    @patch("apps.games.models.GamePlayer")
    def test_streak_not_met(self, mock_gp):
        from apps.achievements.services import _check_win_streak

        qs = MagicMock()
        mock_gp.objects.filter.return_value.order_by.return_value.__getitem__ = lambda s, k: qs
        qs.count.return_value = 1
        result = _check_win_streak(MagicMock(), 3, None, None, None)
        assert result is False


class TestCheckFastAnswers(BaseServiceUnitTest):
    """Vérifie _check_fast_answers."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    @patch("apps.games.models.GameAnswer")
    def test_fast_answers_met(self, mock_ga):
        from apps.achievements.services import _check_fast_answers

        mock_ga.objects.filter.return_value.count.return_value = 10
        assert _check_fast_answers(MagicMock(), 5, "3.0", None, None) is True

    @patch("apps.games.models.GameAnswer")
    def test_fast_answers_not_met(self, mock_ga):
        from apps.achievements.services import _check_fast_answers

        mock_ga.objects.filter.return_value.count.return_value = 2
        assert _check_fast_answers(MagicMock(), 5, None, None, None) is False


class TestCheckAccuracy(BaseServiceUnitTest):
    """Vérifie _check_accuracy."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    @patch("apps.games.models.GameAnswer")
    def test_accuracy_met(self, mock_ga):
        from apps.achievements.services import _check_accuracy

        user = MagicMock(total_games_played=50)
        mock_ga.objects.filter.return_value.count.side_effect = [100, 90]
        assert _check_accuracy(user, 80, "20", None, None) is True

    @patch("apps.games.models.GameAnswer")
    def test_accuracy_not_enough_games(self, mock_ga):
        from apps.achievements.services import _check_accuracy

        user = MagicMock(total_games_played=5)
        assert _check_accuracy(user, 80, "20", None, None) is False

    @patch("apps.games.models.GameAnswer")
    def test_accuracy_zero_answers(self, mock_ga):
        from apps.achievements.services import _check_accuracy

        user = MagicMock(total_games_played=50)
        mock_ga.objects.filter.return_value.count.return_value = 0
        assert _check_accuracy(user, 80, None, None, None) is False


class TestCheckGlobalStreak(BaseServiceUnitTest):
    """Vérifie _check_global_streak."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    def test_from_round_data(self):
        from apps.achievements.services import _check_global_streak

        assert _check_global_streak(MagicMock(), 5, None, None, {"max_streak": 7}) is True
        assert _check_global_streak(MagicMock(), 5, None, None, {"max_streak": 3}) is False

    @patch("apps.games.models.GameAnswer")
    @patch("apps.games.models.GamePlayer")
    def test_from_db(self, mock_gp, mock_ga):
        from apps.achievements.services import _check_global_streak

        mock_gp.objects.filter.return_value.values_list.return_value = ["pid1"]
        mock_ga.objects.filter.return_value.order_by.return_value.values_list.return_value = [
            True, True, True, True, True
        ]
        assert _check_global_streak(MagicMock(), 5, None, None, None) is True


class TestCheckSingleGameScore(BaseServiceUnitTest):
    """Vérifie _check_single_game_score."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    @patch("apps.games.models.GamePlayer")
    def test_score_met(self, mock_gp):
        from apps.achievements.services import _check_single_game_score

        mock_gp.objects.filter.return_value.exists.return_value = True
        assert _check_single_game_score(MagicMock(), 1000, None, None, None) is True


class TestCheckGamesByMode(BaseServiceUnitTest):
    """Vérifie _check_games_by_mode."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    @patch("apps.games.models.GamePlayer")
    def test_met(self, mock_gp):
        from apps.achievements.services import _check_games_by_mode

        mock_gp.objects.filter.return_value.count.return_value = 10
        assert _check_games_by_mode(MagicMock(), 5, "classique", None, None) is True


class TestCheckWinsByMode(BaseServiceUnitTest):
    """Vérifie _check_wins_by_mode."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    @patch("apps.games.models.GamePlayer")
    def test_met(self, mock_gp):
        from apps.achievements.services import _check_wins_by_mode

        mock_gp.objects.filter.return_value.count.return_value = 3
        assert _check_wins_by_mode(MagicMock(), 3, "rapide", None, None) is True


class TestCheckAllModesPlayed(BaseServiceUnitTest):
    """Vérifie _check_all_modes_played."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    @patch("apps.games.models.GamePlayer")
    def test_met(self, mock_gp):
        from apps.achievements.services import _check_all_modes_played

        mock_gp.objects.filter.return_value.values_list.return_value.distinct.return_value.count.return_value = 6
        assert _check_all_modes_played(MagicMock(), 6, None, None, None) is True


class TestCheckFriendsCount(BaseServiceUnitTest):
    """Vérifie _check_friends_count."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    @patch("apps.users.models.Friendship")
    def test_met(self, mock_f):
        from apps.achievements.services import _check_friends_count

        mock_f.objects.filter.return_value.count.return_value = 5
        assert _check_friends_count(MagicMock(), 3, None, None, None) is True


class TestCheckGamesHosted(BaseServiceUnitTest):
    """Vérifie _check_games_hosted."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    @patch("apps.games.models.Game")
    def test_met(self, mock_g):
        from apps.achievements.services import _check_games_hosted

        mock_g.objects.filter.return_value.count.return_value = 10
        assert _check_games_hosted(MagicMock(), 5, None, None, None) is True


class TestCheckInvitationsSent(BaseServiceUnitTest):
    """Vérifie _check_invitations_sent."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    @patch("apps.games.models.GameInvitation")
    def test_met(self, mock_gi):
        from apps.achievements.services import _check_invitations_sent

        mock_gi.objects.filter.return_value.count.return_value = 5
        assert _check_invitations_sent(MagicMock(), 3, None, None, None) is True


class TestCheckItemsPurchased(BaseServiceUnitTest):
    """Vérifie _check_items_purchased."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    @patch("apps.shop.models.UserInventory")
    def test_met(self, mock_ui):
        from apps.achievements.services import _check_items_purchased

        mock_ui.objects.filter.return_value.values.return_value.distinct.return_value.count.return_value = 5
        assert _check_items_purchased(MagicMock(), 3, None, None, None) is True


class TestCheckBonusUsed(BaseServiceUnitTest):
    """Vérifie _check_bonus_used."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    @patch("apps.shop.models.GameBonus")
    def test_met(self, mock_gb):
        from apps.achievements.services import _check_bonus_used

        mock_gb.objects.filter.return_value.count.return_value = 3
        assert _check_bonus_used(MagicMock(), 2, "double_points", None, None) is True


class TestCheckAllBonusesUsed(BaseServiceUnitTest):
    """Vérifie _check_all_bonuses_used."""

    def get_service_module(self):
        import apps.achievements.services
        return apps.achievements.services

    @patch("apps.shop.models.GameBonus")
    @patch("apps.shop.models.BonusType")
    def test_all_used(self, mock_bt, mock_gb):
        from apps.achievements.services import _check_all_bonuses_used

        mock_bt.values = ["double_points", "shield"]
        mock_gb.objects.filter.return_value.exists.return_value = True
        assert _check_all_bonuses_used(MagicMock(), 0, None, None, None) is True

    @patch("apps.shop.models.GameBonus")
    @patch("apps.shop.models.BonusType")
    def test_not_all_used(self, mock_bt, mock_gb):
        from apps.achievements.services import _check_all_bonuses_used

        mock_bt.values = ["double_points", "shield"]
        mock_gb.objects.filter.return_value.exists.side_effect = [True, False]
        assert _check_all_bonuses_used(MagicMock(), 0, None, None, None) is False
