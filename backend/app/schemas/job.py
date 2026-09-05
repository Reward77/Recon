from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class CreateJobRequest(BaseModel):

    job_name: str
    description: Optional[str] = None


class JobResponse(BaseModel):

    id: UUID
    job_name: str
    description: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True