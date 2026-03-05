"""Configuration OpenTelemetry — activée par OTEL_ENABLED=true.

Le module initialise le tracing distribué :
- TracerProvider avec OTLPSpanExporter (vers Jaeger/Tempo)
- Auto-instrumentation Django, Celery, requests
- Propagation W3C TraceContext
"""

import logging
import os

logger = logging.getLogger(__name__)


def setup_otel():
    """Initialise OpenTelemetry si OTEL_ENABLED est activé."""
    if os.environ.get("OTEL_ENABLED", "").lower() not in ("true", "1", "yes"):
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.celery import CeleryInstrumentor
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning(
            "OpenTelemetry packages not installed. "
            "Install with: pip install opentelemetry-api opentelemetry-sdk "
            "opentelemetry-instrumentation-django opentelemetry-instrumentation-celery "
            "opentelemetry-instrumentation-requests opentelemetry-exporter-otlp"
        )
        return

    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")

    resource = Resource.create(
        {
            "service.name": os.environ.get("OTEL_SERVICE_NAME", "instantmusic-backend"),
            "service.version": os.environ.get("APP_VERSION", "dev"),
        }
    )

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Auto-instrumentation
    DjangoInstrumentor().instrument()
    CeleryInstrumentor().instrument()
    RequestsInstrumentor().instrument()

    logger.info("OpenTelemetry tracing initialized — exporting to %s", endpoint)
