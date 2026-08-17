from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class RoadmapTaskOut(BaseModel):
    id: UUID
    week: int
    title: str
    detail: str | None
    position: int
    completed: bool
    completed_at: datetime | None

    class Config:
        from_attributes = True


class RoadmapProgress(BaseModel):
    total: int
    completed: int
    percent: float


class RoadmapTaskUpdate(BaseModel):
    completed: bool


class RoadmapTasksOut(BaseModel):
    recommendation_id: UUID
    gap_id: UUID
    progress: RoadmapProgress
    tasks: list[RoadmapTaskOut]
