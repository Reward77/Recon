from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class CreateProcessorRequest(BaseModel):
    name: str
    description: Optional[str] = None


class ProcessorResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
