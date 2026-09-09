from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

from app.services.llm import LLMError, complete_json, complete_text, get_client

load_dotenv()

# Re-exported so existing imports of get_client keep working.
__all__ = ["generate_question", "evaluate_answer", "AnswerEvaluation", "get_client"]


class AnswerDimensions(BaseModel):
    """Per-dimension grades. See interview_analytics for why these three."""
    technical: int = Field(ge=0, le=10)
    problem_solving: int = Field(ge=0, le=10)
    communication: int = Field(ge=0, le=10)

    @field_validator("technical", "problem_solving", "communication", mode="before")
    @classmethod
    def coerce(cls, v):
        return _coerce_int(v)


class AnswerEvaluation(BaseModel):
    """Shape the evaluation response must conform to before we trust it."""
    score: int = Field(ge=0, le=10)
    feedback: str
    strengths: str = ""
    improvements: str = ""
    # Optional on purpose. The overall score and feedback are the core of an
    # evaluation and remain useful without the breakdown, so a model that omits
    # dimensions degrades to "not measured" rather than failing the whole answer.
    dimensions: AnswerDimensions | None = None

    @field_validator("score", mode="before")
    @classmethod
    def coerce_score(cls, v):
        return _coerce_int(v)


def _coerce_int(v):
    """Models occasionally return "8" or 8.0 instead of 8."""
    if isinstance(v, str):
        v = v.strip()
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return v


def question_prompt(job_role: str, difficulty: str, previous_questions: list[str]) -> str:
    prev = "\n".join(previous_questions) if previous_questions else "None"
    return f"""You are a senior technical interviewer conducting a {difficulty} level interview for a {job_role} position.

Previous questions asked:
{prev}

Generate ONE new interview question that:
- Is different from all previous questions
- Is appropriate for {difficulty} difficulty
- Tests real technical knowledge for a {job_role}
- Is clear and concise

Return ONLY the question, nothing else. No numbering, no explanation."""


def evaluation_prompt(question: str, answer: str, job_role: str) -> str:
    return f"""You are a senior technical interviewer evaluating a candidate's answer for a {job_role} position.

Question: {question}

Candidate's Answer: {answer}

Evaluate the answer and respond in this JSON format only, no extra text:
{{
  "score": <integer from 0 to 10>,
  "feedback": "<2-3 sentences of specific, constructive feedback>",
  "strengths": "<what the candidate did well, one short phrase>",
  "improvements": "<what could be better, one short phrase>",
  "dimensions": {{
    "technical": <0-10>,
    "problem_solving": <0-10>,
    "communication": <0-10>
  }}
}}

Overall scoring guide:
0-3: Poor - missing key concepts
4-6: Average - basic understanding shown
7-8: Good - solid understanding with minor gaps
9-10: Excellent - comprehensive and accurate

Dimension guide — grade each independently, they will differ:
- technical: factual accuracy and depth of the concepts used
- problem_solving: quality of the reasoning and approach, not just the conclusion
- communication: clarity, structure and coherence of the explanation

Grade only what the written answer evidences. Do not infer confidence,
enthusiasm or seniority — this is a typed answer and those are not observable.

Return ONLY the JSON."""


def generate_question(job_role: str, difficulty: str, previous_questions: list[str] = None) -> str:
    """Raises LLMError if the model can't produce a question."""
    return complete_text(
        question_prompt(job_role, difficulty, previous_questions or []),
        max_tokens=800,
        temperature=0.8,
    )


def evaluate_answer(question: str, answer: str, job_role: str) -> dict:
    """Score an answer.

    Raises LLMError when the model returns something unusable. Previously this
    fell back to a hardcoded score of 5, which recorded a fabricated grade
    indistinguishable from a real one.
    """
    evaluation = complete_json(
        evaluation_prompt(question, answer, job_role),
        AnswerEvaluation,
        max_tokens=1000,
        temperature=0.3,
    )
    return evaluation.model_dump()
