"""Tests unitaires du PdfBuilder."""

from unittest.mock import MagicMock, patch

from tests.base import BaseServiceUnitTest


class TestPdfBuilderInit(BaseServiceUnitTest):
    """Vérifie l'initialisation du PdfBuilder."""

    def get_service_module(self):
        from apps.games import pdf_service
        return pdf_service

    def _make_builder(self, **game_overrides):
        from apps.games.pdf_service import PdfBuilder
        game_data = {
            "room_code": "ABCD",
            "name": "Test Game",
            "mode": "classique",
            "mode_display": "Classique",
            "answer_mode_display": "QCM",
            "guess_target_display": "Titre",
            "num_rounds": 5,
            "finished_at": "2025-01-15T14:30:00",
        }
        game_data.update(game_overrides)
        rankings = [
            {"username": "alice", "score": 100, "rank": 1},
            {"username": "bob", "score": 80, "rank": 2},
            {"username": "charlie", "score": 60, "rank": 3},
        ]
        rounds = [
            {
                "round_number": 1,
                "track_name": "Song1",
                "artist_name": "Artist1",
                "correct_answer": "Song1",
                "answers": [
                    {"username": "alice", "answer": "Song1", "is_correct": True,
                     "points_earned": 50, "response_time": 2.5, "bonuses": []},
                ],
            },
        ]
        return PdfBuilder(game_data, rankings, rounds)

    def test_init(self):
        builder = self._make_builder()
        assert builder.room_code == "ABCD"
        assert builder.game_name == "Test Game"
        assert builder.mode_display == "Classique"
        assert builder.date_display != ""

    def test_init_no_name(self):
        builder = self._make_builder(name="")
        assert builder.game_name == ""

    def test_init_no_date(self):
        builder = self._make_builder(finished_at=None, started_at=None)
        assert builder.date_display == ""


class TestPdfBuilderSections(BaseServiceUnitTest):
    """Vérifie les méthodes add_* du PdfBuilder."""

    def get_service_module(self):
        from apps.games import pdf_service
        return pdf_service

    def _make_builder(self):
        from apps.games.pdf_service import PdfBuilder
        game_data = {
            "room_code": "ABCD",
            "name": "Test",
            "mode": "classique",
            "mode_display": "Classique",
            "answer_mode_display": "QCM",
            "guess_target_display": "Titre",
            "num_rounds": 3,
            "finished_at": "2025-01-15T14:30:00",
        }
        rankings = [
            {"username": "alice", "score": 100, "rank": 1, "correct_answers": 3,
             "total_answers": 3, "avg_response_time": 2.5},
            {"username": "bob", "score": 80, "rank": 2, "correct_answers": 2,
             "total_answers": 3, "avg_response_time": 3.0},
            {"username": "charlie", "score": 60, "rank": 3, "correct_answers": 1,
             "total_answers": 3, "avg_response_time": 4.0},
        ]
        rounds = [
            {
                "round_number": 1,
                "track_name": "Song1",
                "artist_name": "Artist1",
                "correct_answer": "Song1",
                "question_type": "guess_title",
                "answers": [
                    {"username": "alice", "answer": "Song1", "is_correct": True,
                     "points_earned": 50, "response_time": 2.5, "bonuses": []},
                    {"username": "bob", "answer": "Wrong", "is_correct": False,
                     "points_earned": 0, "response_time": 5.0, "bonuses": []},
                ],
            },
        ]
        return PdfBuilder(game_data, rankings, rounds)

    def test_add_header(self):
        builder = self._make_builder()
        result = builder.add_header()
        assert result is builder
        assert len(builder.elements) > 0

    def test_add_podium(self):
        builder = self._make_builder()
        result = builder.add_podium()
        assert result is builder
        assert len(builder.elements) > 0

    def test_add_ranking_table(self):
        builder = self._make_builder()
        result = builder.add_ranking_table()
        assert result is builder
        assert len(builder.elements) > 0

    def test_add_round_details(self):
        builder = self._make_builder()
        result = builder.add_round_details()
        assert result is builder
        assert len(builder.elements) > 0

    def test_add_score_chart(self):
        builder = self._make_builder()
        result = builder.add_score_chart()
        assert result is builder
        assert len(builder.elements) > 0

    def test_build_produces_bytes(self):
        builder = self._make_builder()
        pdf_bytes = (
            builder
            .add_header()
            .add_podium()
            .add_ranking_table()
            .add_round_details()
            .add_score_chart()
            .build()
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b"%PDF"


class TestPdfHelpers(BaseServiceUnitTest):
    """Vérifie les helpers du pdf_service."""

    def get_service_module(self):
        from apps.games import pdf_service
        return pdf_service

    def test_medal_labels(self):
        from apps.games.pdf_service import _medal
        assert _medal(1) == "1er"
        assert _medal(2) == "2e"
        assert _medal(3) == "3e"
        assert _medal(4) == "4."

    def test_section_header(self):
        from apps.games.pdf_service import _section_header
        from reportlab.lib.styles import getSampleStyleSheet
        styles = getSampleStyleSheet()
        from reportlab.lib.styles import ParagraphStyle
        sec_sty = ParagraphStyle("sec", parent=styles["Normal"])
        result = _section_header("Test", sec_sty)
        assert result is not None
