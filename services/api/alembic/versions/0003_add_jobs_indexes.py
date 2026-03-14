"""add indexes for jobs.updated_at and jobs.correlation_id"""

from alembic import op

revision = "0003_add_jobs_indexes"
down_revision = "0002_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_jobs_updated_at", "jobs", ["updated_at"])
    op.create_index("ix_jobs_correlation_id", "jobs", ["correlation_id"])


def downgrade() -> None:
    op.drop_index("ix_jobs_correlation_id", table_name="jobs")
    op.drop_index("ix_jobs_updated_at", table_name="jobs")
