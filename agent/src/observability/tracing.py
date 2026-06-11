"""
OpenTelemetry tracing setup for Vibe-Trading.

Environment-variable driven (no-op when not configured):

    OTEL_EXPORTER_OTLP_ENDPOINT  e.g. http://localhost:4317
    OTEL_SERVICE_NAME             default: vibe-trading

When OTEL_EXPORTER_OTLP_ENDPOINT is unset, the SDK creates a NoOp tracer
provider — zero overhead, zero network calls.

Usage:
    from src.observability.tracing import get_tracer, init_tracing

    init_tracing()                  # call once at app startup
    tracer = get_tracer("my.module")

    with tracer.start_as_current_span("operation_name") as span:
        span.set_attribute("key", "value")
        # ...
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

logger = logging.getLogger(__name__)

_TRACER_PROVIDER: Optional[TracerProvider] = None
_INITIALIZED = False


def get_tracer(name: str = "vibe-trading") -> trace.Tracer:
    """Return a tracer for the given instrumenting module name.

    Safe to call before ``init_tracing()`` — returns a no-op tracer
    when the provider hasn't been set up yet.
    """
    return trace.get_tracer(name)


def init_tracing(
    *,
    service_name: str | None = None,
    endpoint: str | None = None,
) -> None:
    """One-time OpenTelemetry SDK initialization.

    When ``endpoint`` is falsy, falls back to the
    ``OTEL_EXPORTER_OTLP_ENDPOINT`` env var.  If that is also unset,
    a no-op provider is installed so the rest of the application can
    call ``get_tracer()`` unconditionally.

    Args:
        service_name: Override for ``OTEL_SERVICE_NAME`` (default: ``vibe-trading``).
        endpoint: Override for ``OTEL_EXPORTER_OTLP_ENDPOINT``.
    """
    global _TRACER_PROVIDER, _INITIALIZED
    if _INITIALIZED:
        logger.debug("init_tracing skipped — already initialised")
        return

    svc = service_name or os.getenv("OTEL_SERVICE_NAME", "vibe-trading")
    ep = endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")

    # Configure resource attributes that appear on every span
    resource = Resource.create({SERVICE_NAME: svc})

    if ep:
        # Real export: gRPC OTLP exporter → Jaeger / OTel Collector
        exporter = OTLPSpanExporter(endpoint=ep, insecure=True)
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _TRACER_PROVIDER = provider
        logger.info("OpenTelemetry tracing enabled → %s (service=%s)", ep, svc)
    else:
        # No-op: safe default when no collector is configured
        logger.debug(
            "OTEL_EXPORTER_OTLP_ENDPOINT not set — tracing is no-op"
        )

    _INITIALIZED = True


def instrument_fastapi(app) -> None:
    """Auto-instrument a FastAPI app for HTTP-level spans.

    Must be called AFTER ``init_tracing()``.
    """
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app, excluded_urls="/health")
        logger.info("FastAPI instrumentation applied")
    except ImportError:
        logger.warning("opentelemetry-instrumentation-fastapi not installed")


def instrument_httpx() -> None:
    """Auto-instrument httpx for outbound HTTP call spans."""
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        HTTPXClientInstrumentor().instrument()
        logger.info("httpx instrumentation applied")
    except ImportError:
        logger.warning("opentelemetry-instrumentation-httpx not installed")
