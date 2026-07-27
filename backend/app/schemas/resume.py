from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class ResumeOut(BaseModel):
    id: UUID
    file_name: str
    ats_score: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

class ResumeDetail(BaseModel):
    id: UUID
    file_name: str
    parsed_text: str | None
    ats_score: int
    uploaded_at: datetime

    class Config:
        from_attributes = True