from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    gap_id = Column(UUID(as_uuid=True), ForeignKey("skill_gaps.id"), nullable=False)
    courses = Column(JSON, default=[])
    projects = Column(JSON, default=[])
    books = Column(JSON, default=[])
    roadmap = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)