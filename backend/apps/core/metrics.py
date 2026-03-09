"""Prometheus metrics endpoint for Django.
"""

import os

from django.http import HttpResponse, HttpResponseForbidden
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

try:
    # In case of Gunicorn with multiple workers (multiprocess mode)
    from prometheus_client import CollectorRegistry, multiprocess
except Exception:
    multiprocess = None  # type: ignore[assignment]
    CollectorRegistry = None  # type: ignore[assignment,misc]


def metrics(request):
    """Return Prometheus metrics in the expected content type.

    Accès restreint au réseau interne (ALLOWED_METRICS_IPS) ou aux staff.
    Use multiprocess registry only when the PROMETHEUS_MULTIPROC_DIR env var
    is set and points to an existing directory. Otherwise fall back to the
    default global registry to avoid ValueError at import/runtime.
    """
    allowed_ips = os.environ.get("ALLOWED_METRICS_IPS", "127.0.0.1,172.16.0.0/12,10.0.0.0/8").split(",")
    client_ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")).split(",")[0].strip()

    from ipaddress import ip_address, ip_network

    is_allowed = False
    try:
        client = ip_address(client_ip)
        for allowed in allowed_ips:
            allowed = allowed.strip()
            try:
                if "/" in allowed:
                    if client in ip_network(allowed, strict=False):
                        is_allowed = True
                        break
                elif client == ip_address(allowed):
                    is_allowed = True
                    break
            except ValueError:
                continue
    except ValueError:
        pass

    if not is_allowed and not (hasattr(request, "user") and request.user.is_authenticated and request.user.is_staff):
        return HttpResponseForbidden("Forbidden")

    mp_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")

    if (
        multiprocess
        and CollectorRegistry is not None
        and mp_dir
        and os.path.isdir(mp_dir)
    ):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
    else:
        # Use default global registry
        from prometheus_client import REGISTRY as registry

    data = generate_latest(registry)
    return HttpResponse(data, content_type=CONTENT_TYPE_LATEST)
