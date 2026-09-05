from sqlalchemy.orm import Session
from uuid import UUID

from app.models.job import ReconciliationJob, JobStatus
from app.models.user import User


class JobNotFoundException(Exception):
    pass


class JobService:

    @staticmethod
    def create_job(
        db: Session,
        current_user: User,
        request
    ):

        job = ReconciliationJob(
            company_id=current_user.company_id,
            created_by=current_user.id,
            job_name=request.job_name,
            description=request.description,
            status=JobStatus.PENDING
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        return job

    @staticmethod
    def get_company_jobs(
        db: Session,
        company_id: UUID
    ):

        return (
            db.query(ReconciliationJob)
            .filter(
                ReconciliationJob.company_id == company_id
            )
            .order_by(
                ReconciliationJob.created_at.desc()
            )
            .all()
        )

    @staticmethod
    def get_job(
        db: Session,
        company_id: UUID,
        job_id: UUID
    ):

        return (
            db.query(ReconciliationJob)
            .filter(
                ReconciliationJob.company_id == company_id,
                ReconciliationJob.id == job_id
            )
            .first()
        )

    @staticmethod
    def delete_job(
        db: Session,
        company_id: UUID,
        job_id: UUID
    ):

        job = (
            db.query(ReconciliationJob)
            .filter(
                ReconciliationJob.company_id == company_id,
                ReconciliationJob.id == job_id
            )
            .first()
        )

        if not job:
            raise JobNotFoundException("Job not found.")

        db.delete(job)
        db.commit()

        return {
            "message": "Job deleted successfully."
        }