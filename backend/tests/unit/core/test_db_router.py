"""Tests unitaires du ReadReplicaRouter."""

from config.db_router import ReadReplicaRouter
from tests.base import BaseUnitTest


class TestReadReplicaRouter(BaseUnitTest):
    """Vérifie le routage lecture/écriture."""

    def get_target_class(self):
        return ReadReplicaRouter

    def setup_method(self):
        self.router = ReadReplicaRouter()

    def test_db_for_read_returns_replica(self):
        assert self.router.db_for_read(None) == "replica"

    def test_db_for_write_returns_default(self):
        assert self.router.db_for_write(None) == "default"

    def test_allow_relation_returns_true(self):
        assert self.router.allow_relation(None, None) is True

    def test_allow_migrate_default(self):
        assert self.router.allow_migrate("default", "users") is True

    def test_allow_migrate_replica_denied(self):
        assert self.router.allow_migrate("replica", "users") is False
