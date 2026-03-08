from fastapi import FastAPI

from app.api.routes import router
from app.core.correlation import CorrelationIdMiddleware
from app.core.logging import configure_logging
from app.core.observability import MetricsMiddleware, configure_tracing, instrument_fastapi

configure_logging()
configure_tracing()

app = FastAPI(title="Quantum Control Plane API")
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(MetricsMiddleware)
app.include_router(router)
instrument_fastapi(app)
