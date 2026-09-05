from sqlalchemy import func

from ..models.reconciliation_result import ReconciliationResult, ReconciliationStatus
from ..models.job import ReconciliationJob
from ..models.upload import Upload


class DashboardService:

    @staticmethod
    def summary(db, job_id):

        total = db.query(func.count(ReconciliationResult.id)).filter(
            ReconciliationResult.job_id == job_id
        ).scalar()

        matched = db.query(func.count(ReconciliationResult.id)).filter(
            ReconciliationResult.job_id == job_id,
            ReconciliationResult.status == ReconciliationStatus.MATCHED
        ).scalar()

        amount = db.query(func.count(ReconciliationResult.id)).filter(
            ReconciliationResult.job_id == job_id,
            ReconciliationResult.status == ReconciliationStatus.AMOUNT_MISMATCH
        ).scalar()

        status = db.query(func.count(ReconciliationResult.id)).filter(
            ReconciliationResult.job_id == job_id,
            ReconciliationResult.status == ReconciliationStatus.STATUS_MISMATCH
        ).scalar()

        missing_company = db.query(func.count(ReconciliationResult.id)).filter(
            ReconciliationResult.job_id == job_id,
            ReconciliationResult.status == ReconciliationStatus.MISSING_IN_COMPANY
        ).scalar()

        missing_processor = db.query(func.count(ReconciliationResult.id)).filter(
            ReconciliationResult.job_id == job_id,
            ReconciliationResult.status == ReconciliationStatus.MISSING_IN_PROCESSOR
        ).scalar()

        return {
            "total": total,
            "matched": matched,
            "amount_mismatch": amount,
            "status_mismatch": status,
            "missing_company": missing_company,
            "missing_processor": missing_processor,
            "success_rate": round(matched / total * 100, 2) if total else 0,
        }

    @staticmethod
    def company_summary(db, company_id):
        # counts across the whole company
        total = db.query(func.count(ReconciliationResult.id)).filter(
            ReconciliationResult.company_id == company_id
        ).scalar()

        matched = db.query(func.count(ReconciliationResult.id)).filter(
            ReconciliationResult.company_id == company_id,
            ReconciliationResult.status == ReconciliationStatus.MATCHED
        ).scalar()

        amount = db.query(func.count(ReconciliationResult.id)).filter(
            ReconciliationResult.company_id == company_id,
            ReconciliationResult.status == ReconciliationStatus.AMOUNT_MISMATCH
        ).scalar()

        status = db.query(func.count(ReconciliationResult.id)).filter(
            ReconciliationResult.company_id == company_id,
            ReconciliationResult.status == ReconciliationStatus.STATUS_MISMATCH
        ).scalar()

        missing_company = db.query(func.count(ReconciliationResult.id)).filter(
            ReconciliationResult.company_id == company_id,
            ReconciliationResult.status == ReconciliationStatus.MISSING_IN_COMPANY
        ).scalar()

        missing_processor = db.query(func.count(ReconciliationResult.id)).filter(
            ReconciliationResult.company_id == company_id,
            ReconciliationResult.status == ReconciliationStatus.MISSING_IN_PROCESSOR
        ).scalar()

        jobs = db.query(func.count(ReconciliationJob.id)).filter(
            ReconciliationJob.company_id == company_id
        ).scalar()

        uploads = db.query(func.count(Upload.id)).filter(
            Upload.company_id == company_id
        ).scalar()

        mismatch = total - matched if total else 0

        return {
            "total": total,
            "matched": matched,
            "mismatch": mismatch,
            "amount_mismatch": amount,
            "status_mismatch": status,
            "missing_company": missing_company,
            "missing_processor": missing_processor,
            "jobs": jobs,
            "uploads": uploads,
            "success_rate": round(matched / total * 100, 2) if total else 0,
        }