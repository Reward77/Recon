import uuid

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Boolean

from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Processor(Base):

    __tablename__ = "processors"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name = Column(
        String(100),
        unique=True,
        nullable=False
    )

    description = Column(
        String(500)
    )

    is_active = Column(
        Boolean,
        default=True
    )