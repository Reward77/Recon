import sys
from pathlib import Path

from fastapi.staticfiles import StaticFiles
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.error_handling import http_exception_handler, validation_exception_handler, unhandled_exception_handler
import uuid
from app.models.job import ReconciliationJob
from app.models.processor import Processor
from app.models.upload import Upload
from app.models.column_mapping import ColumnMapping
from app.models.reconciliation_result import ReconciliationResult
from app.models.password_reset_token import PasswordResetToken
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.models.subscription import Plan, Subscription, BillingPayment, BillingEvent
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.jobs import router as jobs_router
from app.api.users import router as users_router
from app.api.uploads import router as uploads_router
from app.api.processors import router as processors_router
from app.api.mapping import router as mapping_router
from app.api.notifications import router as notifications_router
from app.api.billing import router as billing_router
from app.api.settings import router as settings_router
# Import all models
from app.models.company import Company
from app.models.user import User,UserRole
from app.core.config import settings
from app.core.database import get_db
from app.core.celery_app import celery_app
import sentry_sdk
import logging
logger = logging.getLogger("recon")



app = FastAPI(
    title="Recon API",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.ENVIRONMENT,
                traces_sample_rate=0.1 if settings.is_production else 1.0,
                profiles_sample_rate=0.1 if settings.is_production else 1.0,
                release="recon@1.0.0",
            )
            logger.info("Sentry initialized.")
        except Exception as exc:
            logger.warning("Failed to initialize Sentry: %s", exc)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-Id") or f"req_{uuid.uuid4().hex}"
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    return response


from time import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time()
        window_start = now - self.window_seconds
        self._requests[client_ip] = [t for t in self._requests[client_ip] if t > window_start]
        if len(self._requests[client_ip]) >= self.max_requests:
            return False
        self._requests[client_ip].append(now)
        return True


rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/auth"):
        client_ip = request.client.host if request.client else "unknown"
        if not rate_limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={"title": "Too many requests", "detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": "60"},
            )
    return await call_next(request)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(
        "HTTP %s %s",
        request.method,
        request.url.path,
        extra={"request_id": getattr(request.state, "request_id", None)},
    )
    response = await call_next(request)
    logger.info(
        "HTTP %s %s -> %s",
        request.method,
        request.url.path,
        response.status_code,
        extra={"request_id": getattr(request.state, "request_id", None)},
    )
    return response


app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(dashboard_router)
app.include_router(users_router)
app.include_router(uploads_router)
app.include_router(processors_router)
app.include_router(mapping_router)
app.include_router(notifications_router)
app.include_router(billing_router)
app.include_router(settings_router)

@app.get("/")
def home():
    return {
        "message": "Recon API is running."
    }


@app.get("/health/live")
def health_live():
    return {"status": "alive", "service": "Recon API"}


@app.get("/health/ready")
def health_ready(db=Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    redis_ok = False
    if settings.REDIS_URL:
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL, socket_timeout=2, socket_connect_timeout=2)
            r.ping()
            redis_ok = True
        except Exception:
            redis_ok = False

    celery_ok = False
    if redis_ok:
        try:
            insp = celery_app.control.inspect(timeout=2)
            celery_ok = bool(insp.ping())
        except Exception:
            celery_ok = False

    ready = db_ok and redis_ok and celery_ok
    payload = {
        "status": "ready" if ready else "unavailable",
        "service": "Recon API",
        "checks": {
            "database": "ok" if db_ok else "failed",
            "redis": "ok" if redis_ok else "failed",
            "celery": "ok" if celery_ok else "failed",
        },
    }
    return JSONResponse(content=payload, status_code=200 if ready else 503)


from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
from io import BytesIO
import pandas as pd

from app.core.database import get_db
from app.api.dependencies import get_current_user, require_permission
from app.services.reconciliation_service import ReconciliationService
from app.models.reconciliation_result import ReconciliationResult, ReconciliationStatus

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


def serialize_result(result):
    """Keep the results board and exported files based on the same fields."""
    company_amount = result.company_amount
    processor_amount = result.processor_amount
    difference = (
        processor_amount - company_amount
        if company_amount is not None and processor_amount is not None
        else None
    )
    return {
        "id": str(result.id),
        "transaction_id": result.transaction_id,
        "company_amount": company_amount,
        "processor_amount": processor_amount,
        "difference": difference,
        "company_status": result.company_status,
        "processor_status": result.processor_status,
        "status": result.status.value,
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Recon API"}


def filtered_results(job_id, current_user, db, status=None, search=None):
    query = db.query(ReconciliationResult).filter(
        ReconciliationResult.job_id == job_id,
        ReconciliationResult.company_id == current_user.company_id,
    )
    if status:
        normalized_status = status.upper()
        if normalized_status == "MISSING":
            query = query.filter(ReconciliationResult.status.in_([
                ReconciliationStatus.MISSING_IN_COMPANY,
                ReconciliationStatus.MISSING_IN_PROCESSOR,
            ]))
        else:
            try:
                query = query.filter(ReconciliationResult.status == ReconciliationStatus(normalized_status))
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid result status.")
    if search:
        query = query.filter(ReconciliationResult.transaction_id.ilike(f"%{search.strip()}%"))
    return query.order_by(ReconciliationResult.transaction_id).all()


def create_simple_pdf(rows):
    """Create a dependency-free, printable PDF for reconciliation exports."""
    lines = ["Recon Reconciliation Results", ""]
    for row in rows:
        line = " | ".join([
            str(row["transaction_id"]),
            str(row["company_amount"] if row["company_amount"] is not None else "-"),
            str(row["processor_amount"] if row["processor_amount"] is not None else "-"),
            str(row["difference"] if row["difference"] is not None else "-"),
            row["status"],
        ])
        lines.append(line[:120])
    if len(rows) == 0:
        lines.append("No results match the selected filters.")

    page_lines = [lines[index:index + 44] for index in range(0, len(lines), 44)] or [[]]
    objects = ["<< /Type /Catalog /Pages 2 0 R >>", ""]
    page_ids = []
    content_ids = []
    next_id = 3
    for _ in page_lines:
        page_ids.append(next_id)
        content_ids.append(next_id + 1)
        next_id += 2
    objects[1] = "<< /Type /Pages /Kids [" + " ".join(f"{page_id} 0 R" for page_id in page_ids) + f"] /Count {len(page_ids)} >>"
    for page_id, content_id, page in zip(page_ids, content_ids, page_lines):
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {next_id} 0 R >> >> /Contents {content_id} 0 R >>")
        commands = ["BT /F1 9 Tf 36 756 Td 12 TL"]
        for line in page:
            safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.append(f"({safe_line}) Tj T*")
        commands.append("ET")
        content = "\n".join(commands)
        objects.append(f"<< /Length {len(content.encode('latin-1', 'replace'))} >>\nstream\n{content}\nendstream")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    pdf = "%PDF-1.4\n"
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf.encode("latin-1", "replace")))
        pdf += f"{index} 0 obj\n{obj}\nendobj\n"
    xref = len(pdf.encode("latin-1", "replace"))
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    pdf += "".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:])
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF"
    return pdf.encode("latin-1", "replace")

@router.post("/{job_id}/run")
def run_reconciliation(job_id: UUID, db: Session = Depends(get_db), current_user=Depends(require_permission("reconciliation:run"))):
    try:
        return ReconciliationService.enqueue(db, current_user.company_id, job_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}/results")
def get_reconciliation_results(job_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        results = db.query(ReconciliationResult).filter(
            ReconciliationResult.job_id == job_id,
            ReconciliationResult.company_id == current_user.company_id
        ).all()

        total = len(results)
        matched = sum(1 for r in results if r.status == ReconciliationStatus.MATCHED)
        mismatched = sum(1 for r in results if r.status in [
            ReconciliationStatus.AMOUNT_MISMATCH,
            ReconciliationStatus.STATUS_MISMATCH,
            ReconciliationStatus.DUPLICATE,
        ])
        duplicates = sum(1 for r in results if r.status == ReconciliationStatus.DUPLICATE)
        missing = sum(1 for r in results if r.status in [
            ReconciliationStatus.MISSING_IN_COMPANY,
            ReconciliationStatus.MISSING_IN_PROCESSOR
        ])

        return {
            "total": total,
            "matched": matched,
            "mismatched": mismatched,
            "duplicates": duplicates,
            "missing": missing,
            "results": [
                serialize_result(result)
                for result in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{job_id}/export/excel")
def export_excel(job_id: UUID, status: str | None = Query(None), search: str | None = Query(None), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    rows = [serialize_result(result) for result in filtered_results(job_id, current_user, db, status, search)]
    columns = ["transaction_id", "company_amount", "processor_amount", "difference", "company_status", "processor_status", "status"]
    dataframe = pd.DataFrame(rows, columns=columns).rename(columns={
        "transaction_id": "Transaction ID", "company_amount": "Company Amount",
        "processor_amount": "Processor Amount", "difference": "Difference",
        "company_status": "Company Status", "processor_status": "Processor Status", "status": "Result Status",
    })
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Results")
        worksheet = writer.sheets["Results"]
        worksheet.freeze_panes = "A2"
        for column_cells in worksheet.columns:
            worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(len(str(cell.value or "")) for cell in column_cells) + 2, 28)
    return StreamingResponse(BytesIO(output.getvalue()), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="reconciliation-{job_id}.xlsx"'})


@router.get("/{job_id}/export/pdf")
def export_pdf(job_id: UUID, status: str | None = Query(None), search: str | None = Query(None), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    rows = [serialize_result(result) for result in filtered_results(job_id, current_user, db, status, search)]
    return Response(content=create_simple_pdf(rows), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="reconciliation-{job_id}.pdf"'})

app.include_router(router)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Request-Id", "X-CSRF-Token"],

)
