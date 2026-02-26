"""
Prometheus metrics endpoint for Django.
"""
from django.http import HttpResponse

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

try:
    # In case of Gunicorn with multiple workers (multiprocess mode)
    from prometheus_client import CollectorRegistry, multiprocess
except Exception:
    multiprocess = None
    CollectorRegistry = None


def metrics(request):
    """Return Prometheus metrics in the expected content type."""
    if multiprocess and CollectorRegistry is not None:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
    else:
        # Use default global registry
        from prometheus_client import REGISTRY as registry

    data = generate_latest(registry)
    return HttpResponse(data, content_type=CONTENT_TYPE_LATEST)
