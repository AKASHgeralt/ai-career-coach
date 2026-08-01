from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class StartInterview(BaseModel):
    job_role: str
    difficulty: str = "medium"

class SubmitAnswer(BaseModel):
    session_id: UUID
    answer: str

class SessionOut(BaseModel):
    id: UUID
    job_role: str
    difficulty: str
    total_score: int
    questions_asked: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class AnswerOut(BaseModel):
    id: UUID
    question: str
    answer: str
    score: int
    ai_feedback: str | None
    created_at: datetime

    class Config:
        from_attributes = True