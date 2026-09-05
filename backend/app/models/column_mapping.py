import uuid

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import ForeignKey

from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ColumnMapping(Base):

    __tablename__ = "column_mappings"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False
    )

    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reconciliation_jobs.id"),
        nullable=False
    )

    processor_id = Column(
        UUID(as_uuid=True),
        ForeignKey("processors.id"),
        nullable=False
    )

    company_column = Column(
        String(255),
        nullable=False
    )

    processor_column = Column(
        String(255),
        nullable=False
    )

    canonical_column = Column(
        String(255),
        nullable=False
    )

    # A processor can submit more than one file for a job; mappings belong to
    # the uploaded file, not just to the processor account.
    processor_upload_id = Column(
        UUID(as_uuid=True),
        ForeignKey("uploads.id"),
        nullable=True
    )
