"""Tests unitaires du module encryption."""

from unittest.mock import MagicMock, patch

from apps.users.encryption import decrypt_email, encrypt_email, get_fernet, hash_email
from tests.base import BaseServiceUnitTest


class TestEncryption(BaseServiceUnitTest):
    """Vérifie le chiffrement/déchiffrement et le hachage des emails."""

    def get_service_module(self):
        import apps.users.encryption
        return apps.users.encryption

    # ── get_fernet ──────────────────────────────────────────────────

    @patch("apps.users.encryption.settings")
    @patch("apps.users.encryption.Fernet")
    def test_get_fernet_uses_setting_key(self, mock_fernet_cls, mock_settings):
        mock_settings.EMAIL_ENCRYPTION_KEY = "dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtlejE="
        get_fernet()
        mock_fernet_cls.assert_called_once_with(
            mock_settings.EMAIL_ENCRYPTION_KEY.encode()
        )

    # ── encrypt_email ───────────────────────────────────────────────

    @patch("apps.users.encryption.get_fernet")
    def test_encrypt_email_lowercases(self, mock_get_fernet):
        mock_f = MagicMock()
        mock_f.encrypt.return_value = b"encrypted_token"
        mock_get_fernet.return_value = mock_f

        result = encrypt_email("Alice@Example.COM")
        mock_f.encrypt.assert_called_once_with(b"alice@example.com")
        assert result == "encrypted_token"

    @patch("apps.users.encryption.get_fernet")
    def test_encrypt_email_returns_str(self, mock_get_fernet):
        mock_f = MagicMock()
        mock_f.encrypt.return_value = b"token123"
        mock_get_fernet.return_value = mock_f

        result = encrypt_email("test@test.com")
        assert isinstance(result, str)

    # ── decrypt_email ───────────────────────────────────────────────

    @patch("apps.users.encryption.get_fernet")
    def test_decrypt_email_returns_plain(self, mock_get_fernet):
        mock_f = MagicMock()
        mock_f.decrypt.return_value = b"alice@example.com"
        mock_get_fernet.return_value = mock_f

        result = decrypt_email("encrypted_token")
        mock_f.decrypt.assert_called_once_with(b"encrypted_token")
        assert result == "alice@example.com"

    # ── hash_email ──────────────────────────────────────────────────

    @patch("apps.users.encryption.hmac")
    @patch("apps.users.encryption.settings")
    def test_hash_email_uses_hmac_sha256(self, mock_settings, mock_hmac):
        mock_settings.EMAIL_HASH_KEY = "secret_hash_key"
        mock_digest = MagicMock()
        mock_digest.hexdigest.return_value = "abcdef1234"
        mock_hmac.new.return_value = mock_digest

        result = hash_email("Alice@Example.COM")

        mock_hmac.new.assert_called_once()
        args = mock_hmac.new.call_args
        assert args[0][0] == b"secret_hash_key"
        assert args[0][1] == b"alice@example.com"
        assert result == "abcdef1234"

    @patch("apps.users.encryption.hmac")
    @patch("apps.users.encryption.settings")
    def test_hash_email_lowercases_input(self, mock_settings, mock_hmac):
        mock_settings.EMAIL_HASH_KEY = "key"
        mock_digest = MagicMock()
        mock_digest.hexdigest.return_value = "hash"
        mock_hmac.new.return_value = mock_digest

        hash_email("UPPER@CASE.COM")
        args = mock_hmac.new.call_args
        assert args[0][1] == b"upper@case.com"
