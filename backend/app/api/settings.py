import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import UserRole

router = APIRouter(prefix="/settings", tags=["Settings"])

DEFAULT_PREFERENCES = {
    "currency": "NGN",
    "date_format": "DD/MM/YYYY",
    "amount_tolerance": "0.00",
    "auto_match": True,
    "email_notifications": True,
    "exception_notifications": True,
}


class SettingsUpdate(BaseModel):
    company_name: str = Field(min_length=2, max_length=120)
    company_email: str = Field(min_length=5, max_length=254)
    phone: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=300)
    preferences: dict = Field(default_factory=dict)


def serialize(company):
    try:
        stored = json.loads(company.settings_json or "{}")
    except json.JSONDecodeError:
        stored = {}
    return {
        "company_name": company.company_name,
        "company_email": company.company_email,
        "phone": company.phone or "",
        "address": company.address or "",
        "preferences": {**DEFAULT_PREFERENCES, **stored},
    }


@router.get("")
def get_settings(current_user=Depends(get_current_user)):
    return serialize(current_user.company)


@router.put("")
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only Administrators can update company settings.")
    company = current_user.company
    company.company_name = payload.company_name.strip()
    company.company_email = payload.company_email.strip().lower()
    company.phone = (payload.phone or "").strip() or None
    company.address = (payload.address or "").strip() or None
    company.settings_json = json.dumps({**DEFAULT_PREFERENCES, **payload.preferences})
    db.commit()
    db.refresh(company)
    return serialize(company)
