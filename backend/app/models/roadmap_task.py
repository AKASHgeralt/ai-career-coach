from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database import Base


class RoadmapTask(Base):
    """A single checkable item materialised from a generated roadmap.

    Tasks are derived from the roadmap JSON at generation time rather than
    stored only inside it, so completion state is relational and queryable
    (progress totals, "what's left this week") without rewriting a JSON blob
    on every tick.
    """
    __tablename__ = "roadmap_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recommendation_id = Column(
        UUID(as_uuid=True), ForeignKey("recommendations.id"), nullable=False
    )
    week = Column(Integer, nullable=False, default=1)
    title = Column(Text, nullable=False)
    detail = Column(Text, nullable=True)
    # Ordering within a week, so the list is stable across reloads.
    position = Column(Integer, nullable=False, default=0)
    completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Progress is read per recommendation on every roadmap view and dashboard load.
Index("ix_roadmap_tasks_recommendation_id", RoadmapTask.recommendation_id)
Index("ix_roadmap_tasks_user_id", RoadmapTask.user_id)
