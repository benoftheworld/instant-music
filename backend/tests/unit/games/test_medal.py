"""Tests unitaires des fonctions pures de pdf_service."""

from apps.games.pdf_service import _medal
from tests.base import BaseUnitTest


class TestMedal(BaseUnitTest):
    """Vérifie le formatage des rangs en labels de médaille."""

    def get_target_class(self):
        return _medal

    def test_first_place(self):
        assert _medal(1) == "1er"

    def test_second_place(self):
        assert _medal(2) == "2e"

    def test_third_place(self):
        assert _medal(3) == "3e"

    def test_fourth_place(self):
        assert _medal(4) == "4."

    def test_tenth_place(self):
        assert _medal(10) == "10."
