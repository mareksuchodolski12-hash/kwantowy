import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings
from app.queue.redis_queue import RedisQueue

jobs_submitted_total = Counter("qcp_jobs_submitted_total", "Submitted jobs", ["provider"])
jobs_succeeded_total = Counter("qcp_jobs_succeeded_total", "Succeeded jobs", ["provider"])
jobs_failed_total = Counter("qcp_jobs_failed_total", "Failed jobs", ["provider"])
job_retries_total = Counter("qcp_job_retries_total", "Job retries", ["provider"])
queue_latency_seconds = Histogram("qcp_queue_latency_seconds", "Queue latency seconds", ["provider"])
execution_duration_seconds = Histogram("qcp_execution_duration_seconds", "Execution duration seconds", ["provider"])
dlq_length = Gauge("qcp_dlq_length", "Number of messages in the dead-letter queue")
queue_depth = Gauge("qcp_queue_depth", "Number of messages waiting in the job queue")
processing_count = Gauge("qcp_processing_count", "Number of messages currently being processed")

# ---------------------------------------------------------------------------
# Advanced observability – platform-level metrics (component 8)
# ---------------------------------------------------------------------------

provider_reliability = Gauge(
    "qcp_provider_reliability",
    "Provider reliability ratio (success / total)",
    ["provider"],
)
fidelity_drift = Gauge(
    "qcp_fidelity_drift",
    "Fidelity drift from baseline per provider",
    ["provider"],
)
circuit_optimisation_savings = Histogram(
    "qcp_circuit_optimisation_depth_reduction",
    "Circuit depth reduction achieved by optimiser",
    ["strategy"],
)
workflow_runs_total = Counter(
    "qcp_workflow_runs_total",
    "Total workflow runs",
    ["state"],
)
cost_per_provider = Counter(
    "qcp_cost_usd_total",
    "Cumulative cost in USD per provider",
    ["provider"],
)

_metrics_logger = logging.getLogger(__name__)


async def _refresh_queue_gauges() -> None:
    """Snapshot queue sizes into Prometheus gauges.  Best-effort; errors are logged and swallowed."""
    try:
        redis = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
        try:
            q = RedisQueue(redis)
            dlq_length.set(await q.dlq_length())
            queue_depth.set(await q.queue_length())
            processing_count.set(await q.processing_count())
        finally:
            await redis.close()
    except Exception:
        _metrics_logger.debug("Could not refresh queue gauges", exc_info=True)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/metrics":
            await _refresh_queue_gauges()
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
