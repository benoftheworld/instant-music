"""Tests unitaires du GameService."""

from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from tests.base import BaseServiceUnitTest


class TestGameServiceStartGame(BaseServiceUnitTest):
    """Vérifie start_game dans différents scénarios."""

    def get_service_module(self):
        from apps.games.services import game_service
        return game_service

    def _make_svc(self):
        from apps.games.services.game_service import GameService
        return GameService()

    def test_start_game_not_waiting(self):
        svc = self._make_svc()
        game = MagicMock(status="in_progress")
        with pytest.raises(ValueError):
            svc.start_game(game)

    def test_start_game_no_playlist(self):
        svc = self._make_svc()
        game = MagicMock(status="waiting", mode="classique", playlist_id=None)
        with pytest.raises(ValueError):
            svc.start_game(game)

    @patch("apps.games.services.game_service.GAMES_ACTIVE")
    @patch("apps.games.services.game_service.GAMES_CREATED_TOTAL")
    @patch("apps.games.services.game_service.transaction")
    @patch("apps.games.services.game_service.GameRound")
    @patch("apps.games.services.game_service.timezone")
    def test_start_game_success(self, mock_tz, mock_gr, mock_tx, mock_gc, mock_ga):
        svc = self._make_svc()
        game = MagicMock(
            status="waiting",
            mode="classique",
            playlist_id="123",
            num_rounds=2,
            round_duration=30,
            answer_mode="mcq",
            guess_target="title",
            host=MagicMock(),
        )
        questions = [
            {
                "track_id": "1", "track_name": "Song1", "artist_name": "A1",
                "correct_answer": "Song1", "options": ["Song1", "S2", "S3", "S4"],
                "preview_url": "url", "question_type": "guess_title",
                "question_text": "Q?", "extra_data": {},
            },
            {
                "track_id": "2", "track_name": "Song2", "artist_name": "A2",
                "correct_answer": "Song2", "options": ["Song2", "S1", "S3", "S4"],
                "preview_url": "url", "question_type": "guess_title",
                "question_text": "Q?", "extra_data": {},
            },
        ]
        mock_gr.objects.create.return_value = MagicMock()

        with patch.object(svc, "_generate_questions", return_value=questions):
            result_game, rounds = svc.start_game(game)
        assert result_game.status == "in_progress"

    def test_start_game_no_questions(self):
        svc = self._make_svc()
        game = MagicMock(status="waiting", mode="classique", playlist_id="123")
        with patch.object(svc, "_generate_questions", return_value=[]):
            with pytest.raises(ValueError):
                svc.start_game(game)

    @patch("apps.games.services.game_service.GAMES_ACTIVE")
    @patch("apps.games.services.game_service.GAMES_CREATED_TOTAL")
    @patch("apps.games.services.game_service.transaction")
    @patch("apps.games.services.game_service.get_synced_lyrics")
    @patch("apps.games.services.game_service.get_synced_lyrics_by_lrclib_id")
    @patch("apps.games.services.game_service.GameRound")
    @patch("apps.games.services.game_service.timezone")
    def test_start_karaoke_game(self, mock_tz, mock_gr, mock_lrclib, mock_synced,
                                mock_tx, mock_gc, mock_ga):
        svc = self._make_svc()
        mock_lrclib.return_value = [{"time_ms": 0, "text": "la"}]
        mock_gr.objects.create.return_value = MagicMock()
        game = MagicMock(
            status="waiting",
            mode="karaoke",
            karaoke_track={"youtube_video_id": "yt1", "track_name": "Song",
                           "artist_name": "Art", "duration_ms": 180000,
                           "lrclib_id": 42},
            karaoke_song_id=1,
            answer_mode="mcq",
            guess_target="title",
        )
        result_game, rounds = svc.start_game(game)
        assert result_game.status == "in_progress"

    def test_start_karaoke_no_track(self):
        svc = self._make_svc()
        game = MagicMock(status="waiting", mode="karaoke", karaoke_track=None)
        with pytest.raises(ValueError):
            svc._start_karaoke_game(game)


class TestGameServiceCheckAnswer(BaseServiceUnitTest):
    """Vérifie check_answer pour différents modes."""

    def get_service_module(self):
        from apps.games.services import game_service
        return game_service

    def _make_svc(self):
        from apps.games.services.game_service import GameService
        return GameService()

    def test_generation_exact(self):
        svc = self._make_svc()
        ok, factor = svc.check_answer("generation", "2005", "2005")
        assert ok is True
        assert factor == 1.0

    def test_generation_close(self):
        svc = self._make_svc()
        ok, factor = svc.check_answer("generation", "2007", "2005")
        assert ok is True
        assert factor == 0.75

    def test_generation_far(self):
        svc = self._make_svc()
        ok, factor = svc.check_answer("generation", "2009", "2005")
        assert ok is True
        assert factor == 0.4

    def test_generation_wrong(self):
        svc = self._make_svc()
        ok, factor = svc.check_answer("generation", "2020", "2005")
        assert ok is False
        assert factor == 0.0

    def test_generation_invalid(self):
        svc = self._make_svc()
        ok, factor = svc.check_answer("generation", "abc", "2005")
        assert ok is False

    def test_mcq_correct(self):
        svc = self._make_svc()
        ok, factor = svc.check_answer("classique", "Song1", "Song1", {"answer_mode": "mcq"})
        assert ok is True
        assert factor == 1.0

    def test_mcq_wrong(self):
        svc = self._make_svc()
        ok, factor = svc.check_answer("classique", "Song2", "Song1", {"answer_mode": "mcq"})
        assert ok is False
        assert factor == 0.0

    @patch("apps.games.services.game_service.fuzzy_match")
    def test_text_mode_fuzzy(self, mock_fuzzy):
        mock_fuzzy.return_value = (True, 0.85)
        svc = self._make_svc()
        ok, factor = svc.check_answer("paroles", "answer", "correct", {"answer_mode": "text"})
        assert ok is True
        assert factor == 0.85

    @patch("apps.games.services.game_service.fuzzy_match")
    def test_text_mode_no_match(self, mock_fuzzy):
        mock_fuzzy.return_value = (False, 0.3)
        svc = self._make_svc()
        ok, factor = svc.check_answer("paroles", "answer", "correct", {"answer_mode": "text"})
        assert ok is False
        assert factor == 0.0


class TestGameServiceCheckClassiqueText(BaseServiceUnitTest):
    """Vérifie _check_classique_text_answer."""

    def get_service_module(self):
        from apps.games.services import game_service
        return game_service

    def _make_svc(self):
        from apps.games.services.game_service import GameService
        return GameService()

    @patch("apps.games.services.game_service.fuzzy_match")
    def test_both_artist_and_title(self, mock_fuzzy):
        mock_fuzzy.return_value = (True, 0.9)
        svc = self._make_svc()
        ok, factor = svc._check_classique_text_answer(
            "Artist - Title", "Title",
            {"artist_name": "Artist", "track_name": "Title", "answer_mode": "text"},
        )
        assert ok is True
        assert factor == 2.0

    @patch("apps.games.services.game_service.fuzzy_match")
    def test_title_only(self, mock_fuzzy):
        # First call (artist): no match, second (title): match
        mock_fuzzy.side_effect = [(False, 0.2), (True, 0.9)]
        svc = self._make_svc()
        ok, factor = svc._check_classique_text_answer(
            "Title", "Title",
            {"artist_name": "Artist", "track_name": "Title"},
        )
        assert ok is True
        assert factor == 1.0

    @patch("apps.games.services.game_service.fuzzy_match")
    def test_json_format(self, mock_fuzzy):
        mock_fuzzy.return_value = (True, 0.9)
        svc = self._make_svc()
        import json
        answer = json.dumps({"artist": "Artist", "title": "Title"})
        ok, factor = svc._check_classique_text_answer(
            answer, "Title",
            {"artist_name": "Artist", "track_name": "Title"},
        )
        assert ok is True

    @patch("apps.games.services.game_service.fuzzy_match")
    def test_no_match(self, mock_fuzzy):
        mock_fuzzy.return_value = (False, 0.1)
        svc = self._make_svc()
        ok, factor = svc._check_classique_text_answer(
            "gibberish", "Title",
            {"artist_name": "Artist", "track_name": "Title"},
        )
        assert ok is False
        assert factor == 0.0

    def test_empty_answer(self):
        svc = self._make_svc()
        ok, factor = svc._check_classique_text_answer(
            "", "Title", {"artist_name": "Artist", "track_name": "Title"},
        )
        assert ok is False


class TestGameServiceCalculateScore(BaseServiceUnitTest):
    """Vérifie calculate_score."""

    def get_service_module(self):
        from apps.games.services import game_service
        return game_service

    def _make_svc(self):
        from apps.games.services.game_service import GameService
        return GameService()

    def test_zero_accuracy(self):
        svc = self._make_svc()
        assert svc.calculate_score(0.0, 5.0) == 0

    def test_perfect_fast(self):
        svc = self._make_svc()
        score = svc.calculate_score(1.0, 0.0)
        assert score > 0

    def test_slow_answer(self):
        svc = self._make_svc()
        fast = svc.calculate_score(1.0, 1.0)
        slow = svc.calculate_score(1.0, 25.0)
        assert fast > slow

    def test_double_accuracy(self):
        svc = self._make_svc()
        single = svc.calculate_score(1.0, 5.0)
        double = svc.calculate_score(2.0, 5.0)
        assert double > single


class TestGameServiceRoundHelpers(BaseServiceUnitTest):
    """Vérifie get_current_round, get_next_round, start_round, end_round."""

    def get_service_module(self):
        from apps.games.services import game_service
        return game_service

    def _make_svc(self):
        from apps.games.services.game_service import GameService
        return GameService()

    def test_get_current_round(self):
        svc = self._make_svc()
        game = MagicMock()
        game.rounds.filter.return_value.order_by.return_value.first.return_value = MagicMock()
        result = svc.get_current_round(game)
        assert result is not None

    def test_get_next_round(self):
        svc = self._make_svc()
        game = MagicMock()
        game.rounds.filter.return_value.order_by.return_value.first.return_value = MagicMock()
        result = svc.get_next_round(game)
        assert result is not None

    def test_start_round(self):
        svc = self._make_svc()
        r = MagicMock()
        result = svc.start_round(r)
        r.save.assert_called_once()
        assert result.started_at is not None

    @patch("apps.games.services.game_service.timezone")
    def test_end_round(self, mock_tz):
        svc = self._make_svc()
        r = MagicMock()
        # end_round is decorated with @transaction.atomic, call __wrapped__
        svc.end_round.__wrapped__(svc, r)
        r.save.assert_called_once()


class TestGameServiceSubmitAnswer(BaseServiceUnitTest):
    """Vérifie submit_answer."""

    def get_service_module(self):
        from apps.games.services import game_service
        return game_service

    def _make_svc(self):
        from apps.games.services.game_service import GameService
        return GameService()

    @patch("apps.games.services.game_service.SCORES_EARNED")
    @patch("apps.games.services.game_service.ANSWER_RESPONSE_TIME")
    @patch("apps.games.services.game_service.ANSWERS_TOTAL")
    @patch("apps.games.services.game_service.GameAnswer")
    @patch("apps.games.services.game_service.GamePlayer")
    def test_submit_correct_answer(self, mock_gp, mock_ga, mock_ans_total, mock_ans_rt, mock_scores):
        svc = self._make_svc()
        player = MagicMock(consecutive_correct=0, pk=1)
        round_obj = MagicMock(
            game=MagicMock(mode="classique"),
            correct_answer="Song1",
            extra_data={"answer_mode": "mcq"},
            duration=30,
            round_number=1,
        )
        mock_ga.objects.filter.return_value.count.return_value = 0
        mock_ga.objects.create.return_value = MagicMock()

        result = svc.submit_answer.__wrapped__(svc, player, round_obj, "Song1", 2.5)
        mock_ga.objects.create.assert_called_once()

    @patch("apps.games.services.game_service.SCORES_EARNED")
    @patch("apps.games.services.game_service.ANSWER_RESPONSE_TIME")
    @patch("apps.games.services.game_service.ANSWERS_TOTAL")
    @patch("apps.shop.models.GameBonus")
    @patch("apps.games.services.game_service.GameAnswer")
    @patch("apps.games.services.game_service.GamePlayer")
    def test_submit_wrong_answer(self, mock_gp, mock_ga, mock_gb, mock_ans_total, mock_ans_rt, mock_scores):
        svc = self._make_svc()
        player = MagicMock(consecutive_correct=3, pk=1)
        round_obj = MagicMock(
            game=MagicMock(mode="classique"),
            correct_answer="Song1",
            extra_data={"answer_mode": "mcq"},
            duration=30,
            round_number=1,
        )
        mock_ga.objects.create.return_value = MagicMock()
        mock_gb.objects.filter.return_value.exists.return_value = False

        result = svc.submit_answer.__wrapped__(svc, player, round_obj, "Wrong", 2.5)

        assert player.consecutive_correct == 0


class TestGameServiceFinishGame(BaseServiceUnitTest):
    """Vérifie finish_game."""

    def get_service_module(self):
        from apps.games.services import game_service
        return game_service

    def _make_svc(self):
        from apps.games.services.game_service import GameService
        return GameService()

    @patch("apps.games.services.game_service.GAMES_ACTIVE")
    @patch("apps.games.services.game_service.GAMES_FINISHED_TOTAL")
    @patch("apps.games.services.game_service.check_achievements_async")
    @patch("apps.games.services.game_service.GameAnswer")
    @patch("apps.games.services.game_service.Game")
    @patch("apps.games.services.game_service.GamePlayer")
    def test_finish_game(self, mock_gp, mock_game_cls, mock_ga, mock_check,
                         mock_finished_total, mock_active):
        svc = self._make_svc()
        game = MagicMock(status="in_progress", mode="classique", pk=1,
                         host_id=10, num_rounds=5)
        mock_game_cls.objects.select_for_update.return_value.get.return_value = game

        player1 = MagicMock(score=100, pk=1, user_id=10)
        player2 = MagicMock(score=50, pk=2, user_id=20)
        game.players.order_by.return_value = [player1, player2]
        game.rounds.count.return_value = 5

        mock_ga.objects.filter.return_value.order_by.return_value.values_list.return_value = [
            (1, True, 2.0),
            (2, False, 5.0),
        ]

        mock_gp.objects.bulk_update = MagicMock()

        with patch.object(svc, "_distribute_coins"):
            result = svc.finish_game.__wrapped__(svc, game)
        assert result.status == "finished"

    @patch("apps.games.services.game_service.Game")
    def test_finish_already_finished(self, mock_game_cls):
        svc = self._make_svc()
        game = MagicMock(status="finished", pk=1)
        finished_game = MagicMock(status="finished")
        mock_game_cls.objects.select_for_update.return_value.get.return_value = finished_game
        result = svc.finish_game.__wrapped__(svc, game)
        assert result.status == "finished"


class TestGameServiceHelpers(BaseServiceUnitTest):
    """Vérifie les helpers statiques du GameService."""

    def get_service_module(self):
        from apps.games.services import game_service
        return game_service

    def test_effective_round_duration_karaoke_with_video(self):
        from apps.games.services.game_service import GameService
        result = GameService._effective_round_duration(
            {"extra_data": {"video_duration_ms": 180000}}, True, 30
        )
        assert result > 30

    def test_effective_round_duration_karaoke_no_video(self):
        from apps.games.services.game_service import GameService
        from apps.games.services.scoring import KARAOKE_FALLBACK_DURATION
        result = GameService._effective_round_duration({"extra_data": {}}, True, 30)
        assert result == KARAOKE_FALLBACK_DURATION

    def test_effective_round_duration_normal(self):
        from apps.games.services.game_service import GameService
        result = GameService._effective_round_duration({}, False, 30)
        assert result == 30

    def test_build_extra_data(self):
        from apps.games.services.game_service import GameService
        game = MagicMock(mode="classique", answer_mode="mcq", guess_target="title")
        q = {"extra_data": {}, "artist_name": "Art", "track_name": "Track", "album_image": "img"}
        result = GameService._build_extra_data(q, game)
        assert result["album_image"] == "img"
        assert result["round_mode"] == "classique"

    def test_resolve_options_mcq(self):
        from apps.games.services.game_service import GameService
        result = GameService._resolve_options({"options": ["a", "b"]}, False, False)
        assert result == ["a", "b"]

    def test_resolve_options_karaoke(self):
        from apps.games.services.game_service import GameService
        result = GameService._resolve_options({"options": ["a"]}, True, False)
        assert result == []

    def test_resolve_options_text(self):
        from apps.games.services.game_service import GameService
        result = GameService._resolve_options({"options": ["a"]}, False, True)
        assert result == []
