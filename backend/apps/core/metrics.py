"""
Prometheus metrics endpoint for Django.
"""
from django.http import HttpResponse

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import os

try:
    # In case of Gunicorn with multiple workers (multiprocess mode)
    from prometheus_client import CollectorRegistry, multiprocess
except Exception:
    multiprocess = None
    CollectorRegistry = None


def metrics(request):
    """Return Prometheus metrics in the expected content type.

    Use multiprocess registry only when the PROMETHEUS_MULTIPROC_DIR env var
    is set and points to an existing directory. Otherwise fall back to the
    default global registry to avoid ValueError at import/runtime.
    """
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
