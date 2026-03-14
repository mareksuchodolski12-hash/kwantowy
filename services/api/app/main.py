from fastapi import FastAPI

from app.api.routes import router
from app.core.correlation import CorrelationIdMiddleware
from app.core.logging import configure_logging
from app.core.observability import MetricsMiddleware, configure_tracing, instrument_fastapi

configure_logging()
configure_tracing()

app = FastAPI(
    title="Quantum Control Plane API",
    description=(
        "REST API for the Quantum Control Plane — submit quantum circuits, "
        "manage experiments, orchestrate workflows, and benchmark providers."
    ),
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    license_info={"name": "MIT"},
)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(MetricsMiddleware)
app.include_router(router)
instrument_fastapi(app)
