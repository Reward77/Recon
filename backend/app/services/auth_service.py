import hashlib
import secrets
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.user import User,UserRole
from app.models.password_reset_token import PasswordResetToken
from app.core.config import settings
from app.services.billing_service import BillingService

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)


class AuthService:
    _login_failures = {}
    _login_failures_by_ip = {}

    @staticmethod
    def request_password_reset(db: Session, email: str):
        user = db.query(User).filter(User.email == email).first()
        response = {"message": "If that email is registered, a password reset link has been sent."}
        if not user:
            return response

        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used.is_(False),
        ).update({PasswordResetToken.used: True})
        token = secrets.token_urlsafe(32)
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
        ))
        db.commit()

        reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password.html?token={token}"
        if settings.SMTP_HOST and settings.SMTP_FROM_EMAIL:
            message = EmailMessage()
            message["Subject"] = "Reset your Recon password"
            message["From"] = settings.SMTP_FROM_EMAIL
            message["To"] = user.email
            message.set_content(
                f"Use this link to reset your password (valid for {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes):\n{reset_url}"
            )
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
                if settings.SMTP_USE_TLS:
                    smtp.starttls()
                if settings.SMTP_USERNAME:
                    smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
                smtp.send_message(message)
        elif settings.ENVIRONMENT.lower() != "production":
            response["reset_url"] = reset_url
        return response

    @staticmethod
    def reset_password(db: Session, token: str, password: str):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        record = db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > datetime.utcnow(),
        ).first()
        if not record:
            raise ValueError("This reset link is invalid or has expired.")
        user = db.query(User).filter(User.id == record.user_id).first()
        if not user:
            raise ValueError("This reset link is invalid or has expired.")
        user.password_hash = hash_password(password)
        record.used = True
        db.commit()
        return {"message": "Password reset successfully. You can now sign in."}

    @staticmethod
    def register_company(db: Session, data):

        company_exists = db.query(Company).filter(
            Company.company_email == data.company_email
        ).first()

        if company_exists:
            raise Exception("Company already exists.")

        user_exists = db.query(User).filter(
            User.email == data.admin_email
        ).first()

        if user_exists:
            raise Exception("Administrator email already exists.")

        company = Company(
            company_name=data.company_name,
            company_email=data.company_email,
            phone=data.phone,
            address=data.address
        )

        db.add(company)
        db.flush()

        admin = User(
            company_id=company.id,
            full_name=data.admin_name,
            email=data.admin_email,
            password_hash=hash_password(data.password),
            role=UserRole.ADMIN
        )

        db.add(admin)

        # Each company receives one full-access, company-level trial.
        BillingService.ensure_trial(db, company.id)

        db.commit()
        db.refresh(company)

        return {
            "message": "Company registered successfully.",
            "company_id": str(company.id)
        }

    @staticmethod
    def login(db: Session, request):
        email_key = request.email.lower()
        failure = AuthService._login_failures.get(email_key)
        if failure and failure[1] > datetime.utcnow():
            raise Exception("Too many sign-in attempts. Please try again later.")

        if hasattr(request, "client_host") and request.client_host:
            ip_failure = AuthService._login_failures_by_ip.get(request.client_host)
            if ip_failure and isinstance(ip_failure, tuple) and ip_failure[1] > datetime.utcnow():
                raise Exception("Too many sign-in attempts from this network. Please try again later.")

        user = db.query(User).filter(
            User.email == request.email
        ).first()

        if not user:
            AuthService._record_failed_login(email_key, request)
            raise Exception("Invalid email or password.")

        if not verify_password(
            request.password,
            user.password_hash
        ):
            AuthService._record_failed_login(email_key, request)
            raise Exception("Invalid email or password.")

        AuthService._login_failures.pop(email_key, None)
        if hasattr(request, "client_host") and request.client_host:
            AuthService._login_failures_by_ip.pop(request.client_host, None)

        token = create_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "company_id": str(user.company_id),
                "role": user.role
            }
        )

        return {
            "access_token": token,
            "token_type": "Bearer"
        }

    @staticmethod
    def _record_failed_login(email, request=None):
        key = email.lower()
        attempts = AuthService._login_failures.get(key, (0, datetime.utcnow()))[0] + 1
        expiry = datetime.utcnow() + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
        AuthService._login_failures[key] = (attempts, expiry if attempts >= settings.LOGIN_MAX_ATTEMPTS else datetime.utcnow())

        if request and hasattr(request, "client_host") and request.client_host:
            ip = request.client_host
            ip_attempts = AuthService._login_failures_by_ip.get(ip, 0) + 1
            AuthService._login_failures_by_ip[ip] = ip_attempts
            if ip_attempts >= settings.LOGIN_MAX_ATTEMPTS * 3:
                AuthService._login_failures_by_ip[ip] = (ip_attempts, expiry)
