"""Tests unitaires de EncryptedEmailField."""

from unittest.mock import MagicMock, patch

from apps.users.fields import EncryptedEmailField
from tests.base import BaseUnitTest


class TestEncryptedEmailField(BaseUnitTest):
    """Vérifie le chiffrement/déchiffrement des emails."""

    def get_target_class(self):
        return EncryptedEmailField

    def setup_method(self):
        self.field = EncryptedEmailField()

    @patch("apps.users.fields.decrypt_email")
    def test_from_db_value_decrypts(self, mock_decrypt):
        mock_decrypt.return_value = "test@example.com"
        result = self.field.from_db_value("encrypted_value", None, None)
        assert result == "test@example.com"
        mock_decrypt.assert_called_once_with("encrypted_value")

    def test_from_db_value_none(self):
        result = self.field.from_db_value(None, None, None)
        assert result is None

    @patch("apps.users.fields.decrypt_email")
    def test_from_db_value_decrypt_fails_returns_original(self, mock_decrypt):
        mock_decrypt.side_effect = Exception("bad key")
        result = self.field.from_db_value("plain_text", None, None)
        assert result == "plain_text"

    @patch("apps.users.fields.decrypt_email")
    def test_from_db_value_fernet_token_logs_error(self, mock_decrypt):
        mock_decrypt.side_effect = Exception("bad key")
        with patch("apps.users.fields.logger") as mock_logger:
            result = self.field.from_db_value("gAAAAAtest_token", None, None)
            assert result == "gAAAAAtest_token"
            mock_logger.error.assert_called_once()

    @patch("apps.users.fields.encrypt_email")
    def test_get_prep_value_encrypts(self, mock_encrypt):
        mock_encrypt.return_value = "encrypted"
        result = self.field.get_prep_value("test@example.com")
        assert result == "encrypted"
        mock_encrypt.assert_called_once_with("test@example.com")

    def test_get_prep_value_none(self):
        result = self.field.get_prep_value(None)
        assert result is None

    def test_get_prep_value_already_fernet_skips(self):
        # Values starting with "gAAAAA" should not be re-encrypted
        result = self.field.get_prep_value("gAAAAAexisting_token")
        assert result == "gAAAAAexisting_token"

    def test_formfield_returns_email_field(self):
        from django import forms

        formfield = self.field.formfield()
        assert isinstance(formfield, forms.EmailField)
