from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class ResumeOut(BaseModel):
    id: UUID
    file_name: str
    ats_score: int
    version: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

class ResumeDetail(BaseModel):
    id: UUID
    file_name: str
    parsed_text: str | None
    ats_score: int
    version: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ResumeVersionSummary(BaseModel):
    id: UUID
    version: int
    file_name: str
    ats_score: int
    uploaded_at: datetime


class ResumeVersionHistory(BaseModel):
    versions: list[ResumeVersionSummary]
    count: int
    # Null with fewer than two versions — a single point is not an improvement.
    improvement: int | None = None
    latest_version: int | None = None


class ComparedResume(BaseModel):
    id: UUID
    version: int
    file_name: str
    ats_score: int
    uploaded_at: datetime
    skill_count: int


class CategoryDelta(BaseModel):
    key: str
    label: str
    before: int
    after: int
    delta: int
    max: int
    # improved | declined | unchanged
    status: str
    suggestion: str | None = None


class ResumeComparison(BaseModel):
    base: ComparedResume
    target: ComparedResume
    ats_delta: int
    ats_status: str
    skills_gained: list[str]
    skills_lost: list[str]
    skills_kept: list[str]
    # Skills the user's target role expects that the newer version still lacks.
    still_missing: list[str]
    categories: list[CategoryDelta]
    summary: str
