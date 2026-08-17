from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database import Base

class SkillGap(Base):
    __tablename__ = "skill_gaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    job_title = Column(String, nullable=True)
    job_description = Column(Text, nullable=False)
    matched_skills = Column(JSON, default=[])
    missing_skills = Column(JSON, default=[])
    # Per-skill [{skill, status: MATCHED|PARTIAL|MISSING, similarity}].
    # Null for analyses run before classification existed.
    skill_details = Column(JSON, nullable=True)
    match_score = Column(Float, default=0.0)
    used_role_fallback = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)