"""Routeur de base de données pour la réplication lecture/écriture.

Toutes les écritures vont sur la base « default » (primary).
Les lectures sont routées vers « replica » si configurée, sinon « default ».

Activation dans settings :
    DATABASE_ROUTERS = ["config.db_router.ReadReplicaRouter"]
"""


class ReadReplicaRouter:
    """Route les lectures vers la replica, les écritures vers le primary."""

    def db_for_read(self, model, **hints):
        """Return the replica database alias for read operations."""
        return "replica"

    def db_for_write(self, model, **hints):
        """Return the default database alias for write operations."""
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations between objects from either database."""
        # Les objets des deux bases peuvent être liés
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Allow migrations only on the primary database."""
        # Les migrations ne s'exécutent que sur le primary
        return db == "default"
