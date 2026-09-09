from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=False)
    # The uploaded PDF itself is not retained: nothing reads it back, and the
    # deploy targets have ephemeral disks, so storing it promised a durability
    # that did not exist. parsed_text is the extracted content everything uses.
    parsed_text = Column(Text, nullable=True)
    ats_score = Column(Integer, default=0)
    # Per-user sequential version number (v1, v2, v3…), assigned at upload so
    # progress between drafts can be tracked and compared.
    version = Column(Integer, nullable=False, default=1)
    uploaded_at = Column(DateTime, default=datetime.utcnow)