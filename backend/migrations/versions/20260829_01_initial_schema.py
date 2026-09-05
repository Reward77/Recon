"""Create the Recon application schema.

Revision ID: 20260829_01
Revises:
Create Date: 2026-08-29 00:00:00
"""

from alembic import op
from app.core.database import Base
from app.models import audit_log, column_mapping, company, job, notification
from app.models import password_reset_token, processor, reconciliation_result, subscription, upload, user

revision = "20260829_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the schema represented by the initial application models."""
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    """Remove all application tables, including their PostgreSQL enum types."""
    Base.metadata.drop_all(bind=op.get_bind())
