import uuid

from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import DateTime, Text

from sqlalchemy.orm import relationship

from sqlalchemy.dialects.postgresql import UUID

from datetime import datetime

from app.core.database import Base


class Company(Base):

    __tablename__ = "companies"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    company_name = Column(
        String,
        nullable=False,
        unique=True
    )

    company_email = Column(
        String,
        unique=True,
        nullable=False
    )

    phone = Column(String)

    address = Column(String)

    subscription_plan = Column(
        String,
        default="Free"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    users = relationship(
        "User",
        back_populates="company"
    )

    settings_json = Column(Text, nullable=False, default="{}")
