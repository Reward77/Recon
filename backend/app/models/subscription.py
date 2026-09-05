import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Plan(Base):
    __tablename__ = "plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    currency = Column(String(3), nullable=False, default="NGN")
    amount_kobo = Column(Integer, nullable=False)
    interval = Column(String, nullable=False)
    trial_days = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    gateway_plan_code = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    provider = Column(String, nullable=False, default="internal")
    provider_customer_code = Column(String, nullable=True)
    provider_subscription_code = Column(String, nullable=True, unique=True)
    provider_subscription_token = Column(String, nullable=True)
    status = Column(String, nullable=False, index=True)
    trial_started_at = Column(DateTime, nullable=True)
    trial_ends_at = Column(DateTime, nullable=True)
    current_period_started_at = Column(DateTime, nullable=True)
    current_period_ends_at = Column(DateTime, nullable=True)
    grace_ends_at = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    cancelled_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class BillingPayment(Base):
    __tablename__ = "billing_payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=True)
    provider = Column(String, nullable=False)
    provider_reference = Column(String, nullable=False, unique=True)
    provider_transaction_id = Column(String, nullable=True)
    provider_invoice_code = Column(String, nullable=True)
    amount_kobo = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default="NGN")
    status = Column(String, nullable=False, default="PENDING")
    payment_channel = Column(String, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)
    provider_payload = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class BillingEvent(Base):
    __tablename__ = "billing_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String, nullable=False)
    provider_event_id = Column(String, nullable=False, unique=True)
    event_type = Column(String, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    payload = Column(Text, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    processing_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
