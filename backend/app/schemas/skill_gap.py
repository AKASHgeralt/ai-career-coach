from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class SkillGapRequest(BaseModel):
    resume_id: UUID
    # Optional: when blank, the caller's saved target role supplies the title
    # used to pick a baseline skill profile.
    job_title: str = ""
    job_description: str

class SkillDetail(BaseModel):
    skill: str
    # MATCHED | PARTIAL | MISSING
    status: str
    similarity: float


class SkillGapOut(BaseModel):
    id: UUID
    resume_id: UUID
    job_title: str | None
    matched_skills: list
    missing_skills: list
    # Null for analyses run before per-skill classification existed.
    skill_details: list[SkillDetail] | None = None
    match_score: float
    used_role_fallback: bool = False
    created_at: datetime

    class Config:
        from_attributes = True