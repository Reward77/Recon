import hashlib
import hmac
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.subscription import BillingEvent, BillingPayment, Subscription
from app.models.user import UserRole
from app.services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["Billing"])


class CheckoutRequest(BaseModel):
    plan: str = "PRO_MONTHLY"


def require_billing_admin(current_user=Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only Administrators can manage billing.")
    return current_user


@router.get("/entitlement")
def entitlement(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return BillingService.serialize_entitlement(db, current_user.company_id)


@router.get("/payments")
def payments(db: Session = Depends(get_db), current_user=Depends(require_billing_admin)):
    rows = db.query(BillingPayment).filter(BillingPayment.company_id == current_user.company_id).order_by(BillingPayment.created_at.desc()).all()
    return [{"reference": row.provider_reference, "amount_kobo": row.amount_kobo, "currency": row.currency, "status": row.status, "paid_at": row.paid_at, "created_at": row.created_at} for row in rows]


@router.post("/checkout")
def checkout(request: CheckoutRequest, db: Session = Depends(get_db), current_user=Depends(require_billing_admin)):
    try:
        return BillingService.begin_checkout(db, current_user.company, current_user.email, request.plan)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/verify/{reference}")
def verify(reference: str, db: Session = Depends(get_db), current_user=Depends(require_billing_admin)):
    payment = BillingService.verify_reference(db, current_user.company_id, reference)
    return {"reference": payment.provider_reference, "status": payment.status}


@router.post("/cancel")
def cancel(db: Session = Depends(get_db), current_user=Depends(require_billing_admin)):
    subscription, _, _ = BillingService.entitlement(db, current_user.company_id)
    if subscription.status not in {"ACTIVE", "PAST_DUE"}:
        raise HTTPException(status_code=400, detail="There is no active Pro subscription to cancel.")
    try:
        BillingService.cancel_provider_subscription(subscription)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    subscription.cancel_at_period_end = True
    subscription.status = "CANCEL_AT_PERIOD_END"
    subscription.cancelled_at = datetime.utcnow()
    db.commit()
    return {"status": subscription.status, "current_period_ends_at": subscription.current_period_ends_at}


@router.post("/webhooks/paystack")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    secret = settings.PAYSTACK_WEBHOOK_SECRET or settings.PAYSTACK_SECRET_KEY
    signature = request.headers.get("x-paystack-signature", "")
    if not secret or not hmac.compare_digest(signature, hmac.new(secret.encode(), raw, hashlib.sha512).hexdigest()):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")
    payload = json.loads(raw.decode("utf-8"))
    data = payload.get("data", {})
    event_id = str(data.get("id") or data.get("reference") or hashlib.sha256(raw).hexdigest())
    if db.query(BillingEvent).filter(BillingEvent.provider_event_id == event_id).first():
        return {"ok": True, "duplicate": True}
    event = BillingEvent(provider="paystack", provider_event_id=event_id, event_type=payload.get("event", "unknown"), payload=raw.decode("utf-8"))
    db.add(event)
    reference = data.get("reference")
    try:
        if payload.get("event") == "charge.success" and reference:
            payment = db.query(BillingPayment).filter(BillingPayment.provider_reference == reference).first()
            if payment:
                BillingService.apply_success(db, payment, data)
        elif payload.get("event") == "subscription.create":
            customer_code = data.get("customer", {}).get("customer_code")
            subscription = db.query(Subscription).filter(Subscription.provider_customer_code == customer_code).first()
            if subscription:
                subscription.provider = "paystack"
                subscription.provider_subscription_code = data.get("subscription_code") or subscription.provider_subscription_code
                subscription.provider_subscription_token = data.get("email_token") or subscription.provider_subscription_token
        elif payload.get("event") == "invoice.payment_failed":
            BillingService.record_failure(db, data.get("subscription", {}).get("subscription_code"))
        elif payload.get("event") == "subscription.not_renew":
            code = data.get("subscription_code")
            subscription = db.query(Subscription).filter(Subscription.provider_subscription_code == code).first()
            if subscription:
                subscription.status = "CANCEL_AT_PERIOD_END"
        elif payload.get("event") == "subscription.disable":
            code = data.get("subscription_code")
            subscription = db.query(Subscription).filter(Subscription.provider_subscription_code == code).first()
            if subscription:
                subscription.status = "CANCELLED"
                subscription.ended_at = datetime.utcnow()
        event.processed_at = datetime.utcnow()
        db.commit()
    except Exception as error:
        event.processing_error = str(error)
        db.commit()
        raise
    return {"ok": True}
