from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QCP_", env_file=".env", extra="ignore")

    app_name: str = "quantum-control-plane-api"
    environment: str = "dev"
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

    # Worker settings
    stuck_job_timeout_seconds: int = 120


settings = Settings()
