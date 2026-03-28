#!/bin/sh
set -e

echo "[entrypoint] Running database migrations…"
cd /app/services/api
python -m alembic upgrade head
echo "[entrypoint] Migrations complete."

echo "[entrypoint] Ensuring API key is registered…"
python -c "
import asyncio, os
from app.db.session import SessionLocal
from app.repositories.api_keys import ApiKeyRepository

DEFAULT_DEV_KEY = 'qcp_dev_default_key'

async def seed():
    raw = os.environ.get('QCP_API_KEY') or DEFAULT_DEV_KEY
    async with SessionLocal() as session:
        repo = ApiKeyRepository(session)
        await repo.ensure_raw_key(raw, 'default-dev-key')
        await session.commit()
    print('[entrypoint] API key registered and ready.')

asyncio.run(seed())
"

echo "[entrypoint] Starting API server…"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
