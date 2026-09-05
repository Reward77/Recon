from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("")
def list_notifications(unread_only: bool = False, limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Notification).filter(Notification.company_id == current_user.company_id)
    query = query.filter((Notification.user_id.is_(None)) | (Notification.user_id == current_user.id))
    if unread_only:
        query = query.filter(Notification.read.is_(False))
    return [{"id": str(item.id), "title": item.title, "message": item.message, "level": item.level,
             "read": item.read, "created_at": item.created_at} for item in query.order_by(Notification.created_at.desc()).limit(limit)]

@router.post("/{notification_id}/read")
def mark_read(notification_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    item = db.query(Notification).filter(Notification.id == notification_id, Notification.company_id == current_user.company_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Notification not found.")
    item.read = True
    db.commit()
    return {"message": "Notification marked as read."}
