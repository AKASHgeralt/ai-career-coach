from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database import Base

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_role = Column(String, nullable=False)
    difficulty = Column(String, default="medium")
    total_score = Column(Integer, default=0)
    questions_asked = Column(Integer, default=0)
    status = Column(String, default="active")
    # The question the candidate is currently looking at and has not answered yet.
    # Persisted so the answer is graded against the question actually shown to
    # them, rather than one regenerated server-side. Null once the session ends.
    current_question = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    score = Column(Integer, default=0)
    ai_feedback = Column(Text, nullable=True)
    # Per-dimension 0-10 scores, e.g. {"technical": 8, "problem_solving": 7,
    # "communication": 6}. Null for answers graded before dimensions existed.
    dimensions = Column(JSON, nullable=True)
    strengths = Column(Text, nullable=True)
    improvements = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)