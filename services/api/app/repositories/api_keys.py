import hashlib
import secrets
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ApiKeyModel


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def generate_api_key() -> str:
    return "qcp_" + secrets.token_urlsafe(32)


class ApiKeyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str) -> tuple[str, ApiKeyModel]:
        """Create a new API key. Returns (raw_key, model)."""
        raw = generate_api_key()
        now = datetime.now(UTC)
        model = ApiKeyModel(
            key_hash=_hash_key(raw),
            name=name,
            is_active=True,
            created_at=now,
        )
        self.session.add(model)
        await self.session.flush()
        return raw, model

    async def get_by_raw_key(self, raw: str) -> ApiKeyModel | None:
        key_hash = _hash_key(raw)
        result: ApiKeyModel | None = await self.session.scalar(
            select(ApiKeyModel).where(ApiKeyModel.key_hash == key_hash, ApiKeyModel.is_active.is_(True))
        )
        return result

    async def touch(self, key_id: UUID) -> None:
        model = await self.session.get(ApiKeyModel, key_id)
        if model:
            model.last_used_at = datetime.now(UTC)
            await self.session.flush()

    async def revoke(self, key_id: UUID) -> bool:
        model = await self.session.get(ApiKeyModel, key_id)
        if model is None:
            return False
        model.is_active = False
        await self.session.flush()
        return True

    async def ensure_raw_key(self, raw: str, name: str) -> ApiKeyModel:
        """Ensure a specific raw key exists in the database. Idempotent."""
        key_hash = _hash_key(raw)
        existing = await self.session.scalar(
            select(ApiKeyModel).where(ApiKeyModel.key_hash == key_hash)
        )
        if existing:
            return existing
        now = datetime.now(UTC)
        model = ApiKeyModel(
            key_hash=key_hash,
            name=name,
            is_active=True,
            created_at=now,
        )
        self.session.add(model)
        await self.session.flush()
        return model

    async def list(self) -> list[ApiKeyModel]:
        rows = await self.session.scalars(select(ApiKeyModel).order_by(ApiKeyModel.created_at.desc()))
        return list(rows)
