"""Local development launcher — runs the full stack without Docker.

Uses SQLite instead of PostgreSQL and fakeredis instead of Redis.
All async work runs inside uvicorn's event loop (startup event) to
avoid cross-event-loop issues with SQLAlchemy and fakeredis.
"""

import asyncio
import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Configure environment BEFORE any app imports
# ---------------------------------------------------------------------------
_DB_PATH = Path(__file__).parent / "local_dev.db"
os.environ["QCP_DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB_PATH}"
os.environ["QCP_REDIS_URL"] = "redis://localhost:6379/0"  # overridden below
os.environ["QCP_ENVIRONMENT"] = "dev"

# Add services/api to sys.path so the `app` package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services", "api"))

# ---------------------------------------------------------------------------
# 2. Patch Redis dependency with a shared fakeredis instance
# ---------------------------------------------------------------------------
import fakeredis.aioredis  # noqa: E402
from redis.asyncio import Redis  # noqa: E402

_fake_redis: Redis = fakeredis.aioredis.FakeRedis()  # type: ignore[assignment]

from app.api import deps  # noqa: E402

_original_get_redis = deps.get_redis


async def _get_fake_redis() -> AsyncGenerator[Redis, None]:
    yield _fake_redis


deps.get_redis = _get_fake_redis  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# 3. Import the FastAPI app and apply dependency override
# ---------------------------------------------------------------------------
from app.main import app  # noqa: E402

app.dependency_overrides[_original_get_redis] = _get_fake_redis


# ---------------------------------------------------------------------------
# 4. Background worker coroutine (runs in uvicorn's event loop)
# ---------------------------------------------------------------------------
async def _worker_loop() -> None:
    from app.db.session import SessionLocal
    from app.queue.redis_queue import RedisQueue
    from app.services.worker_service import WorkerService

    queue = RedisQueue(_fake_redis)
    while True:
        try:
            item = await queue.dequeue(timeout=1)
            if item is None:
                await asyncio.sleep(0.5)
                continue
            job_id, correlation_id = item
            async with SessionLocal() as session:
                worker = WorkerService(session, queue)
                await worker.process_job(job_id, correlation_id)
        except Exception as e:
            print(f"[WORKER] Error: {e}")
            await asyncio.sleep(2)


# ---------------------------------------------------------------------------
# 5. Startup event — create tables, seed API key, launch worker task
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def _on_startup() -> None:
    import app.db.models  # noqa: F401 — register all models
    from app.db.base import Base
    from app.db.session import SessionLocal, engine
    from app.repositories.api_keys import ApiKeyRepository

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] SQLite tables created")

    # Seed API key (deterministic — same approach as Docker entrypoint)
    DEFAULT_DEV_KEY = "qcp_dev_default_key"
    raw_key = os.environ.get("QCP_API_KEY") or DEFAULT_DEV_KEY
    async with SessionLocal() as session:
        repo = ApiKeyRepository(session)
        await repo.ensure_raw_key(raw_key, "local-dev-key")
        await session.commit()
    print(f"[OK] API key registered: local-dev-key")

    # Write apps/web/.env.local so the frontend can authenticate
    env_local = Path(__file__).parent / "apps" / "web" / ".env.local"
    env_local.write_text(
        f"NEXT_PUBLIC_API_URL=http://localhost:8000\nQCP_API_KEY={raw_key}\n"
    )
    print(f"[OK] Wrote {env_local}")

    # Launch background worker as an asyncio task
    asyncio.create_task(_worker_loop())
    print("[OK] Background worker started")


# ---------------------------------------------------------------------------
# 6. Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  Quantum Control Plane — Local Development Mode")
    print("  (SQLite + fakeredis, no Docker needed)")
    print("=" * 60)
    print()
    print("  API:     http://localhost:8000")
    print("  Docs:    http://localhost:8000/docs")
    print("  Web UI:  cd apps/web && npm run dev")
    print()

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
