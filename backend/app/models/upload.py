import uuid
import enum

import hashlib
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Enum
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import BigInteger
from sqlalchemy.sql import func

from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class UploadType(str, enum.Enum):
    COMPANY = "COMPANY"
    PROCESSOR = "PROCESSOR"


class UploadStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"


class Upload(Base):

    __tablename__ = "uploads"

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
        nullable=True
    )

    original_filename = Column(
        String(255),
        nullable=False
    )

    stored_filename = Column(
        String(255),
        nullable=False
    )

    storage_path = Column(
        String(500),
        nullable=False
    )

    file_size = Column(
        BigInteger,
        nullable=False
    )

    upload_type = Column(
        Enum(UploadType),
        nullable=False
    )

    status = Column(
        Enum(UploadStatus),
        default=UploadStatus.UPLOADED
    )

    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )


    checksum = Column(
    String(64),
    nullable=False
    )

    mime_type = Column(
    String(100),
    nullable=False
    )