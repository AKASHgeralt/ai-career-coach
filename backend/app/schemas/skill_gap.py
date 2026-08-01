from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class SkillGapRequest(BaseModel):
    resume_id: UUID
    job_title: str
    job_description: str

class SkillGapOut(BaseModel):
    id: UUID
    resume_id: UUID
    job_title: str | None
    matched_skills: list
    missing_skills: list
    match_score: float
    created_at: datetime

    class Config:
        from_attributes = True