FROM python:3.12-slim

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app
COPY packages/contracts /app/packages/contracts
COPY services/api /app/services/api
COPY workers/quantum-runner /app/workers/quantum-runner
RUN pip install --no-cache-dir -e /app/packages/contracts && pip install --no-cache-dir -e /app/services/api

USER appuser
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
    CMD python -c "import os, signal; os.kill(1, 0)" || exit 1
CMD ["python", "workers/quantum-runner/runner/main.py"]
