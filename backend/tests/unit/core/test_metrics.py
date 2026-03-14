"""Tests unitaires du endpoint Prometheus metrics."""

from unittest.mock import MagicMock, patch

from tests.base import BaseServiceUnitTest


class TestMetricsAllowedIp(BaseServiceUnitTest):
    """Vérifie le contrôle d'accès IP du endpoint metrics."""

    def get_service_module(self):
        import apps.core.metrics
        return apps.core.metrics

    @patch("apps.core.metrics.generate_latest", return_value=b"metric 1")
    @patch.dict("os.environ", {"ALLOWED_METRICS_IPS": "127.0.0.1", "PROMETHEUS_MULTIPROC_DIR": ""})
    def test_allowed_ip(self, mock_gen):
        from apps.core.metrics import metrics

        request = MagicMock()
        request.META = {"REMOTE_ADDR": "127.0.0.1"}
        request.user = MagicMock(is_authenticated=False)
        response = metrics(request)
        assert response.status_code == 200

    @patch.dict("os.environ", {"ALLOWED_METRICS_IPS": "127.0.0.1"})
    def test_forbidden_ip(self):
        from apps.core.metrics import metrics

        request = MagicMock()
        request.META = {"REMOTE_ADDR": "8.8.8.8"}
        request.user = MagicMock(is_authenticated=False, is_staff=False)
        response = metrics(request)
        assert response.status_code == 403

    @patch("apps.core.metrics.generate_latest", return_value=b"metric 1")
    @patch.dict("os.environ", {"ALLOWED_METRICS_IPS": "127.0.0.1", "PROMETHEUS_MULTIPROC_DIR": ""})
    def test_staff_user_allowed(self, mock_gen):
        from apps.core.metrics import metrics

        request = MagicMock()
        request.META = {"REMOTE_ADDR": "8.8.8.8"}
        request.user = MagicMock(is_authenticated=True, is_staff=True)
        response = metrics(request)
        assert response.status_code == 200

    @patch("apps.core.metrics.generate_latest", return_value=b"metric 1")
    @patch.dict("os.environ", {"ALLOWED_METRICS_IPS": "10.0.0.0/8", "PROMETHEUS_MULTIPROC_DIR": ""})
    def test_cidr_range(self, mock_gen):
        from apps.core.metrics import metrics

        request = MagicMock()
        request.META = {"REMOTE_ADDR": "10.1.2.3"}
        request.user = MagicMock(is_authenticated=False)
        response = metrics(request)
        assert response.status_code == 200

    @patch.dict("os.environ", {"ALLOWED_METRICS_IPS": "10.0.0.0/8"})
    def test_invalid_client_ip(self):
        from apps.core.metrics import metrics

        request = MagicMock()
        request.META = {"REMOTE_ADDR": "not_an_ip"}
        request.user = MagicMock(is_authenticated=False, is_staff=False)
        response = metrics(request)
        assert response.status_code == 403
