from sqlalchemy import Column, String, DateTime, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    # Avatar bytes live in the database, not on disk: the deploy targets have
    # ephemeral filesystems and restart often, which silently emptied the
    # upload folder while avatar_url kept pointing into it. avatar_url is now
    # the API route that serves these bytes back.
    avatar_url = Column(String, nullable=True)
    avatar_data = Column(LargeBinary, nullable=True)
    avatar_mime = Column(String, nullable=True)
    # Slug from app.services.roles.TARGET_ROLES. Drives skill-gap baselines,
    # roadmap generation, interview questions and the readiness score.
    target_role = Column(String, nullable=True)
    target_role_updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)