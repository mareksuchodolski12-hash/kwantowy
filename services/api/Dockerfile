FROM python:3.12-slim

WORKDIR /app
COPY packages/contracts /app/packages/contracts
COPY services/api /app/services/api
RUN pip install --no-cache-dir -e /app/packages/contracts && pip install --no-cache-dir -e /app/services/api

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
