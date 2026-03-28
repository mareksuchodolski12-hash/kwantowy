import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


_PRODUCTION_ENVS = {"production", "prod", "staging"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QCP_", env_file=".env", extra="ignore")

    app_name: str = "quantum-control-plane-api"
    environment: str = "dev"
    # Local-dev fallback only; always set QCP_DATABASE_URL in production.
    database_url: str = "postgresql+asyncpg://quantum:quantum@localhost:5432/quantum_control_plane"
    redis_url: str = "redis://localhost:6379/0"
    queue_name: str = "quantum.jobs"

    default_provider: str = "local_simulator"

    ibm_runtime_enabled: bool = False
    ibm_runtime_channel: str = "ibm_quantum"
    ibm_runtime_token: str | None = None
    ibm_runtime_instance: str | None = None
    ibm_runtime_backend: str = "ibmq_qasm_simulator"

    otel_exporter_otlp_endpoint: str | None = None

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"

    # Worker settings
    stuck_job_timeout_seconds: int = 120


settings = Settings()

# ── Production guard ──────────────────────────────────────────────────────
# Refuse to start with default dev credentials in production-like environments.
if settings.environment.lower() in _PRODUCTION_ENVS:
    _defaults = {
        "database_url": "postgresql+asyncpg://quantum:quantum@localhost:5432/quantum_control_plane",
        "redis_url": "redis://localhost:6379/0",
    }
    for _field, _default in _defaults.items():
        if getattr(settings, _field) == _default:
            sys.exit(
                f"FATAL: QCP_{_field.upper()} is still the local-dev default. "
                f"Set it explicitly for environment={settings.environment!r}."
            )
