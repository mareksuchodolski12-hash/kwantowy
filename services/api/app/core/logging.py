import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "correlation_id"):
            payload["correlation_id"] = record.correlation_id
        if hasattr(record, "job_id"):
            payload["job_id"] = record.job_id
        if hasattr(record, "provider"):
            payload["provider"] = record.provider
        if hasattr(record, "execution_time"):
            payload["execution_time"] = record.execution_time
        return json.dumps(payload)


def configure_logging() -> None:
    from app.core.config import settings

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
