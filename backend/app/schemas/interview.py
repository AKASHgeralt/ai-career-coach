from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class StartInterview(BaseModel):
    # Optional: when blank, falls back to the caller's saved target role.
    job_role: str = ""
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

class DimensionScore(BaseModel):
    key: str
    label: str
    description: str
    # None when no answer in the session recorded this dimension.
    score: float | None = None
    answers_scored: int = 0


class InterviewAnalyticsOut(BaseModel):
    session_id: UUID
    job_role: str
    difficulty: str
    status: str
    questions_answered: int
    overall: float | None = None
    dimensions: list[DimensionScore]
    weakest_dimension: str | None = None
    strongest_dimension: str | None = None
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommended_practice: list[str]
