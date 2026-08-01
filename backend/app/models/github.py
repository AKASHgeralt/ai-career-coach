from sqlalchemy import Column, String, Integer, DateTime, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database import Base

class GitHubProfile(Base):
    __tablename__ = "github_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    github_username = Column(String, nullable=False)
    repo_count = Column(Integer, default=0)
    total_stars = Column(Integer, default=0)
    top_languages = Column(JSON, default=[])
    repos = Column(JSON, default=[])
    developer_score = Column(Float, default=0.0)
    followers = Column(Integer, default=0)
    following = Column(Integer, default=0)
    synced_at = Column(DateTime, default=datetime.utcnow)