"""Multi-tenant platform hierarchy.

Implements the tenant model:

    org → team → project → experiment

This provides the foundation for the platform to evolve into a multi-tenant
SaaS offering.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from quantum_contracts import Organisation, Project, Team
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OrganisationModel, ProjectModel, TeamModel

logger = logging.getLogger(__name__)


class TenantRepository:
    """CRUD operations for the multi-tenant hierarchy."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Organisations ---

    async def create_org(self, name: str) -> Organisation:
        model = OrganisationModel(name=name, created_at=datetime.now(UTC))
        self.session.add(model)
        await self.session.flush()
        return Organisation(id=model.id, name=model.name, created_at=model.created_at)

    async def get_org(self, org_id: UUID) -> Organisation | None:
        row = await self.session.scalar(select(OrganisationModel).where(OrganisationModel.id == org_id))
        if not row:
            return None
        return Organisation(id=row.id, name=row.name, created_at=row.created_at)

    async def list_orgs(self, limit: int = 100) -> list[Organisation]:
        rows = await self.session.scalars(
            select(OrganisationModel).order_by(OrganisationModel.created_at.desc()).limit(limit)
        )
        return [Organisation(id=r.id, name=r.name, created_at=r.created_at) for r in rows]

    # --- Teams ---

    async def create_team(self, org_id: UUID, name: str) -> Team:
        model = TeamModel(org_id=org_id, name=name, created_at=datetime.now(UTC))
        self.session.add(model)
        await self.session.flush()
        return Team(id=model.id, org_id=model.org_id, name=model.name, created_at=model.created_at)

    async def get_team(self, team_id: UUID) -> Team | None:
        row = await self.session.scalar(select(TeamModel).where(TeamModel.id == team_id))
        if not row:
            return None
        return Team(id=row.id, org_id=row.org_id, name=row.name, created_at=row.created_at)

    async def list_teams(self, org_id: UUID, limit: int = 100) -> list[Team]:
        rows = await self.session.scalars(
            select(TeamModel).where(TeamModel.org_id == org_id).order_by(TeamModel.created_at.desc()).limit(limit)
        )
        return [Team(id=r.id, org_id=r.org_id, name=r.name, created_at=r.created_at) for r in rows]

    # --- Projects ---

    async def create_project(self, team_id: UUID, name: str, description: str | None = None) -> Project:
        model = ProjectModel(team_id=team_id, name=name, description=description, created_at=datetime.now(UTC))
        self.session.add(model)
        await self.session.flush()
        return Project(
            id=model.id,
            team_id=model.team_id,
            name=model.name,
            description=model.description,
            created_at=model.created_at,
        )

    async def get_project(self, project_id: UUID) -> Project | None:
        row = await self.session.scalar(select(ProjectModel).where(ProjectModel.id == project_id))
        if not row:
            return None
        return Project(
            id=row.id, team_id=row.team_id, name=row.name, description=row.description, created_at=row.created_at
        )

    async def list_projects(self, team_id: UUID, limit: int = 100) -> list[Project]:
        rows = await self.session.scalars(
            select(ProjectModel)
            .where(ProjectModel.team_id == team_id)
            .order_by(ProjectModel.created_at.desc())
            .limit(limit)
        )
        return [
            Project(id=r.id, team_id=r.team_id, name=r.name, description=r.description, created_at=r.created_at)
            for r in rows
        ]
