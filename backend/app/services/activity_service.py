import smtplib
from email.message import EmailMessage
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.company import Company
from app.models.user import User
from app.core.config import settings


class ActivityService:
    @staticmethod
    def audit(db, company_id, user_id, action, entity_type, entity_id=None, details=None):
        db.add(AuditLog(company_id=company_id, user_id=user_id, action=action,
                        entity_type=entity_type, entity_id=str(entity_id) if entity_id else None,
                        details=details or {}))

    @staticmethod
    def notify(db, company_id, title, message, level="info", user_id=None):
        db.add(Notification(company_id=company_id, user_id=user_id, title=title,
                            message=message, level=level))

    @staticmethod
    def send_email(to_email, subject, body):
        if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
            return
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to_email
            msg.set_content(body)
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
                if settings.SMTP_USE_TLS:
                    smtp.starttls()
                if settings.SMTP_USERNAME:
                    smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
                smtp.send_message(msg)
        except Exception:
            pass

    @staticmethod
    def notify_error(db, company_id, user_id, title, message, error=None):
        ActivityService.notify(db, company_id, title, message, "error", user_id)
        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            ActivityService.send_email(
                company.company_email,
                f"[Recon] {title}",
                f"{message}\n\nError: {error}\n\nTime: {__import__('datetime').datetime.utcnow().isoformat()}",
            )
