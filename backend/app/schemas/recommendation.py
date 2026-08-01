from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class RoadmapRequest(BaseModel):
    gap_id: UUID
    target_role: str

class RecommendationOut(BaseModel):
    id: UUID
    gap_id: UUID
    courses: list
    projects: list
    books: list
    roadmap: list
    created_at: datetime

    class Config:
        from_attributes = True