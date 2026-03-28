FROM python:3.12-slim

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app
COPY packages/contracts /app/packages/contracts
COPY services/api /app/services/api
RUN pip install --no-cache-dir -e /app/packages/contracts && pip install --no-cache-dir -e /app/services/api

COPY services/api/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"
WORKDIR /app/services/api
CMD ["/app/entrypoint.sh"]
