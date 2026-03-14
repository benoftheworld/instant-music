"""Classes abstraites de base pour les tests — Design Pattern Abstract (ABC).

Chaque classe de test du projet hérite de l'une de ces classes abstraites
afin de mutualiser les helpers et réduire la duplication de code.
"""

from abc import ABC, abstractmethod
from unittest.mock import MagicMock

from rest_framework.test import APIClient

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                        TESTS UNITAIRES                              ║
# ╚══════════════════════════════════════════════════════════════════════╝


class BaseUnitTest(ABC):
    """Classe abstraite pour tous les tests unitaires.

    Pas de base de données, pas de réseau — tout est mocké.
    """

    @abstractmethod
    def get_target_class(self):
        """Retourne la classe ou fonction sous test."""

    # ── Helpers d'assertion ─────────────────────────────────────────────

    def assert_field_exists(self, model_class, field_name: str):
        """Vérifie qu'un champ existe sur un modèle Django."""
        field_names = [f.name for f in model_class._meta.get_fields()]
        assert field_name in field_names, (
            f"Le champ '{field_name}' n'existe pas sur {model_class.__name__}. "
            f"Champs disponibles : {field_names}"
        )

    def assert_field_type(self, model_class, field_name: str, expected_type):
        """Vérifie le type d'un champ Django."""
        field = model_class._meta.get_field(field_name)
        assert isinstance(field, expected_type), (
            f"Le champ '{field_name}' est de type {type(field).__name__}, "
            f"attendu {expected_type.__name__}"
        )

    def assert_field_max_length(self, model_class, field_name: str, expected: int):
        """Vérifie le max_length d'un champ CharField."""
        field = model_class._meta.get_field(field_name)
        assert field.max_length == expected, (
            f"{field_name}.max_length = {field.max_length}, attendu {expected}"
        )

    def assert_field_default(self, model_class, field_name: str, expected):
        """Vérifie la valeur par défaut d'un champ."""
        field = model_class._meta.get_field(field_name)
        assert field.default == expected, (
            f"{field_name}.default = {field.default}, attendu {expected}"
        )

    def assert_field_blank(self, model_class, field_name: str, expected: bool):
        """Vérifie si un champ accepte les valeurs vides."""
        field = model_class._meta.get_field(field_name)
        assert field.blank == expected, (
            f"{field_name}.blank = {field.blank}, attendu {expected}"
        )

    def assert_field_null(self, model_class, field_name: str, expected: bool):
        """Vérifie si un champ accepte NULL."""
        field = model_class._meta.get_field(field_name)
        assert field.null == expected, (
            f"{field_name}.null = {field.null}, attendu {expected}"
        )

    def assert_field_unique(self, model_class, field_name: str, expected: bool):
        """Vérifie si un champ est unique."""
        field = model_class._meta.get_field(field_name)
        assert field.unique == expected, (
            f"{field_name}.unique = {field.unique}, attendu {expected}"
        )

    def assert_field_choices(self, model_class, field_name: str, expected_choices):
        """Vérifie les choices d'un champ."""
        field = model_class._meta.get_field(field_name)
        assert field.choices == expected_choices, (
            f"{field_name}.choices differ from expected"
        )

    def assert_field_db_index(self, model_class, field_name: str, expected: bool):
        """Vérifie si un champ a un index DB."""
        field = model_class._meta.get_field(field_name)
        assert field.db_index == expected, (
            f"{field_name}.db_index = {field.db_index}, attendu {expected}"
        )

    def assert_unique_together(self, model_class, expected_fields: list):
        """Vérifie la contrainte unique_together."""
        unique_together = model_class._meta.unique_together
        assert tuple(expected_fields) in unique_together, (
            f"unique_together {expected_fields} non trouvé. "
            f"Actuel : {unique_together}"
        )

    def assert_ordering(self, model_class, expected_ordering: list):
        """Vérifie l'ordering par défaut du modèle."""
        assert list(model_class._meta.ordering) == expected_ordering, (
            f"ordering = {model_class._meta.ordering}, attendu {expected_ordering}"
        )

    def assert_verbose_name(self, model_class, expected: str):
        """Vérifie le verbose_name du modèle."""
        actual = str(model_class._meta.verbose_name)
        assert actual == expected, (
            f"verbose_name = '{actual}', attendu '{expected}'"
        )


class BaseModelUnitTest(BaseUnitTest):
    """Classe abstraite pour les tests unitaires de modèles Django.

    Teste les métadonnées et l'introspection des champs sans accès DB.
    """

    @abstractmethod
    def get_model_class(self):
        """Retourne la classe du modèle Django sous test."""

    def get_target_class(self):
        return self.get_model_class()

    def assert_model_has_uuid_pk(self):
        """Vérifie que le modèle utilise un UUID comme PK."""
        from django.db import models
        pk_field = self.get_model_class()._meta.pk
        assert isinstance(pk_field, models.UUIDField), (
            f"PK de type {type(pk_field).__name__}, attendu UUIDField"
        )
        assert not pk_field.editable, "PK UUIDField ne devrait pas être editable"

    def assert_meta_verbose_name(self, singular: str, plural: str):
        """Vérifie verbose_name et verbose_name_plural."""
        meta = self.get_model_class()._meta
        assert str(meta.verbose_name) == singular
        assert str(meta.verbose_name_plural) == plural

    def assert_str_representation(self, instance, expected: str):
        """Vérifie la représentation __str__ d'une instance."""
        assert str(instance) == expected


class BaseSerializerUnitTest(BaseUnitTest):
    """Classe abstraite pour les tests unitaires de serializers DRF.

    Teste la validation des données sans accès DB.
    """

    @abstractmethod
    def get_serializer_class(self):
        """Retourne la classe du serializer DRF sous test."""

    def get_target_class(self):
        return self.get_serializer_class()

    def assert_valid_data(self, data: dict, context: dict | None = None):
        """Vérifie que les données sont valides pour le serializer."""
        ctx = context or {}
        serializer = self.get_serializer_class()(data=data, context=ctx)
        assert serializer.is_valid(), (
            f"Données attendues valides mais erreurs : {serializer.errors}"
        )
        return serializer

    def assert_invalid_data(
        self, data: dict, expected_field: str, context: dict | None = None
    ):
        """Vérifie que les données sont invalides et que l'erreur est sur le bon champ."""
        ctx = context or {}
        serializer = self.get_serializer_class()(data=data, context=ctx)
        assert not serializer.is_valid(), "Données attendues invalides mais validées"
        assert expected_field in serializer.errors, (
            f"Erreur attendue sur '{expected_field}', erreurs reçues : "
            f"{list(serializer.errors.keys())}"
        )
        return serializer

    def assert_field_read_only(self, field_name: str):
        """Vérifie qu'un champ est read_only."""
        serializer = self.get_serializer_class()()
        field = serializer.fields[field_name]
        assert field.read_only, f"Le champ '{field_name}' devrait être read_only"

    def assert_field_required(self, field_name: str):
        """Vérifie qu'un champ est required."""
        serializer = self.get_serializer_class()()
        field = serializer.fields[field_name]
        assert field.required, f"Le champ '{field_name}' devrait être required"

    def assert_field_not_required(self, field_name: str):
        """Vérifie qu'un champ n'est pas required."""
        serializer = self.get_serializer_class()()
        field = serializer.fields[field_name]
        assert not field.required, f"Le champ '{field_name}' ne devrait pas être required"


class BaseServiceUnitTest(BaseUnitTest):
    """Classe abstraite pour les tests unitaires de services.

    Tout est mocké — pas de DB, pas de réseau.
    """

    @abstractmethod
    def get_service_module(self):
        """Retourne le module du service sous test."""

    def get_target_class(self):
        return self.get_service_module()


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                      TESTS D'INTÉGRATION                            ║
# ╚══════════════════════════════════════════════════════════════════════╝


class BaseIntegrationTest(ABC):
    """Classe abstraite pour les tests d'intégration.

    Utilise une vraie DB (SQLite in-memory via pytest-django).
    Vérifie les réponses HTTP complètes (status code, JSON, headers).
    """

    @abstractmethod
    def get_base_url(self) -> str:
        """Retourne l'URL de base de l'API sous test (ex: '/api/users/')."""

    def get_client(self) -> APIClient:
        """Retourne un client API non authentifié."""
        return APIClient()

    def get_auth_client(self, user) -> APIClient:
        """Retourne un client API authentifié."""
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    # ── Helpers d'assertion HTTP ───────────────────────────────────────

    def assert_status(self, response, expected_status: int):
        """Vérifie le code HTTP de la réponse."""
        assert response.status_code == expected_status, (
            f"Status code = {response.status_code}, attendu {expected_status}. "
            f"Body: {getattr(response, 'data', getattr(response, 'content', ''))}"
        )

    def assert_json_keys(self, response, expected_keys: list):
        """Vérifie que la réponse JSON contient les clés attendues."""
        data = response.json() if hasattr(response, "json") else response.data
        for key in expected_keys:
            assert key in data, (
                f"Clé '{key}' absente de la réponse. Clés présentes : {list(data.keys())}"
            )

    def assert_json_value(self, response, key: str, expected_value):
        """Vérifie une valeur spécifique dans la réponse JSON."""
        data = response.json() if hasattr(response, "json") else response.data
        assert data.get(key) == expected_value, (
            f"data['{key}'] = {data.get(key)}, attendu {expected_value}"
        )

    def assert_error_response(self, response, expected_status: int):
        """Vérifie une réponse d'erreur (status code + présence d'un message)."""
        self.assert_status(response, expected_status)

    def assert_list_response(self, response, min_count: int = 0):
        """Vérifie une réponse de liste."""
        self.assert_status(response, 200)
        data = response.json() if hasattr(response, "json") else response.data
        # Support paginated and non-paginated responses
        if isinstance(data, dict) and "results" in data:
            results = data["results"]
        elif isinstance(data, list):
            results = data
        else:
            results = data
        assert len(results) >= min_count, (
            f"Nombre de résultats = {len(results)}, attendu >= {min_count}"
        )

    def assert_content_type(self, response, expected: str):
        """Vérifie le Content-Type de la réponse."""
        content_type = response.get("Content-Type", "")
        assert expected in content_type, (
            f"Content-Type = '{content_type}', attendu '{expected}'"
        )


class BaseAPIIntegrationTest(BaseIntegrationTest):
    """Classe abstraite pour les tests CRUD d'API REST.

    Étend BaseIntegrationTest avec des helpers pour les patterns CRUD.
    """

    def get_detail_url(self, pk) -> str:
        """Retourne l'URL de détail d'une ressource."""
        return f"{self.get_base_url()}{pk}/"

    def assert_create_success(self, client, data: dict, expected_status: int = 201):
        """Vérifie qu'une création réussit."""
        response = client.post(self.get_base_url(), data, format="json")
        self.assert_status(response, expected_status)
        return response

    def assert_create_failure(
        self, client, data: dict, expected_status: int = 400
    ):
        """Vérifie qu'une création échoue."""
        response = client.post(self.get_base_url(), data, format="json")
        self.assert_status(response, expected_status)
        return response
