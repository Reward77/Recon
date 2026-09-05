from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class UploadResponse(BaseModel):

    id: UUID

    job_id: UUID

    processor_id: UUID | None

    original_filename: str

    stored_filename: str

    upload_type: str

    file_size: int

    status: str

    uploaded_at: datetime

    class Config:
        from_attributes = True
