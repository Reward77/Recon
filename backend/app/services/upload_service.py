import os
import uuid
from pathlib import Path
import hashlib

from fastapi import UploadFile
from app.models.job import ReconciliationJob
from app.models.upload import Upload
from app.models.upload import Upload
from app.models.upload import UploadStatus
from app.models.upload import UploadType
from app.models.processor import Processor

from app.core.config import (
    ALLOWED_EXTENSIONS,
    MAX_UPLOAD_SIZE,
    UPLOAD_ROOT
)


class UploadService:

    @staticmethod
    def validate_extension(file: UploadFile):

        extension = Path(file.filename).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:

            raise Exception(
                "Unsupported file type."
            )

        return extension

    @staticmethod
    async def validate_size(file: UploadFile):

        contents = await file.read()

        size = len(contents)

        await file.seek(0)

        if size > MAX_UPLOAD_SIZE:

            raise Exception(
                "File exceeds maximum size."
            )

        return size

    @staticmethod
    def generate_filename(extension):

        return f"{uuid.uuid4()}{extension}"


    @staticmethod
    def create_storage_path(
        company_id,
        job_id
    ):

        folder = (
            UPLOAD_ROOT
            / str(company_id)
            / str(job_id)
        )

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        return folder


    @staticmethod
    async def save_file(
        file: UploadFile,
        folder,
        filename
    ):

        destination = folder / filename

        with open(destination, "wb") as buffer:

            buffer.write(
                await file.read()
            )

        return destination

    @staticmethod
    async def upload(
        file,
        company_id,
        job_id
    ):

        extension = UploadService.validate_extension(file)

        size = await UploadService.validate_size(file)

        filename = UploadService.generate_filename(extension)

        folder = UploadService.create_storage_path(
            company_id,
            job_id
        )

        path = await UploadService.save_file(
            file,
            folder,
            filename
        )

        return {
            "filename": filename,
            "path": str(path),
            "size": size
        }
    @staticmethod

    async def generate_checksum(file):

        data = await file.read()

        await file.seek(0)

        return hashlib.sha256(data).hexdigest()

    
    @staticmethod
    def validate_job(
        db,
        company_id,
        job_id
    ):

        job = (
        db.query(ReconciliationJob)
        .filter(
            ReconciliationJob.id == job_id,
            ReconciliationJob.company_id == company_id
        )
        .first()
       )

        if not job:
           raise Exception(
           "Job not found."
        )

        return job

    @staticmethod
    def duplicate_exists(
        db,
        job_id,
      checksum
    ):

        return (
            db.query(Upload)
            .filter(
            Upload.job_id == job_id,
            Upload.checksum == checksum
            )
           .first()
        )
    @staticmethod



    def create_upload_record(
         db,
        current_user,
        job_id,
        processor_id,
        upload_type,
        original_filename,
        stored_filename,
        storage_path,
        checksum,
        mime_type,
        size
    ):

        upload = Upload(

        company_id=current_user.company_id,

        job_id=job_id,

        processor_id=processor_id,

        uploaded_by=current_user.id,

        original_filename=original_filename,

        stored_filename=stored_filename,

        storage_path=storage_path,

        checksum=checksum,

        mime_type=mime_type,

        file_size=size,

        upload_type=upload_type,

        status=UploadStatus.UPLOADED
    )

        db.add(upload)

        db.commit()

        db.refresh(upload)

        return upload

    @staticmethod
    async def upload_company(
        db,
        current_user,
        job_id,
        file
    ):

        # ensure job exists and belongs to company
        UploadService.validate_job(db, current_user.company_id, job_id)

        checksum = await UploadService.generate_checksum(file)

        if UploadService.duplicate_exists(db, job_id, checksum):
            raise Exception('Duplicate file uploaded.')

        saved = await UploadService.upload(file, current_user.company_id, job_id)

        mime_type = getattr(file, 'content_type', '') or ''

        upload = UploadService.create_upload_record(
            db,
            current_user,
            job_id,
            None,
            UploadType.COMPANY,
            file.filename,
            saved['filename'],
            saved['path'],
            checksum,
            mime_type,
            saved['size']
        )

        return upload

    @staticmethod
    async def upload_processor(
        db,
        current_user,
        job_id,
        processor_id,
        file
    ):

        # ensure job exists
        UploadService.validate_job(db, current_user.company_id, job_id)

        # ensure processor exists
        proc = db.query(Processor).filter(Processor.id == processor_id).first()
        if not proc:
            raise Exception('Processor not found.')

        checksum = await UploadService.generate_checksum(file)

        if UploadService.duplicate_exists(db, job_id, checksum):
            raise Exception('Duplicate file uploaded.')

        saved = await UploadService.upload(file, current_user.company_id, job_id)

        mime_type = getattr(file, 'content_type', '') or ''

        upload = UploadService.create_upload_record(
            db,
            current_user,
            job_id,
            processor_id,
            UploadType.PROCESSOR,
            file.filename,
            saved['filename'],
            saved['path'],
            checksum,
            mime_type,
            saved['size']
        )

        return upload