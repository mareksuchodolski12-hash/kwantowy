import time
from collections.abc import Awaitable, Callable

from fastapi import Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings

jobs_submitted_total = Counter("qcp_jobs_submitted_total", "Submitted jobs", ["provider"])
jobs_succeeded_total = Counter("qcp_jobs_succeeded_total", "Succeeded jobs", ["provider"])
jobs_failed_total = Counter("qcp_jobs_failed_total", "Failed jobs", ["provider"])
job_retries_total = Counter("qcp_job_retries_total", "Job retries", ["provider"])
queue_latency_seconds = Histogram("qcp_queue_latency_seconds", "Queue latency seconds", ["provider"])
execution_duration_seconds = Histogram("qcp_execution_duration_seconds", "Execution duration seconds", ["provider"])


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/metrics":
            return Response(generate_latest(), media_type="text/plain; version=0.0.4")
        started = time.monotonic()
        response = await call_next(request)
        response.headers["X-Request-Duration-ms"] = str(int((time.monotonic() - started) * 1000))
        return response


def configure_tracing() -> None:
    if not settings.otel_exporter_otlp_endpoint:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": settings.app_name}))
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def instrument_fastapi(app) -> None:  # type: ignore[no-untyped-def]
    FastAPIInstrumentor.instrument_app(app)
