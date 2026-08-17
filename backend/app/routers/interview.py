from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from app.models.interview import InterviewSession, InterviewAnswer
from app.schemas.interview import (
    StartInterview, SubmitAnswer, SessionOut, AnswerOut, InterviewAnalyticsOut,
)
from app.routers.users import get_current_user
from app.models.user import User
from app.services.interview_engine import generate_question, evaluate_answer
from app.services.llm import LLMError
from app.services.roles import role_label
from app.services.interview_analytics import build_session_analytics

router = APIRouter(prefix="/api/interview", tags=["Interview"])

MAX_QUESTIONS = 5

@router.post("/start")
def start_interview(
    request: StartInterview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job_role = (request.job_role or "").strip() or role_label(current_user.target_role)
    if not job_role:
        raise HTTPException(
            status_code=400,
            detail="Provide a job role, or set a target role in Settings first."
        )

    # Generate before persisting so a failed generation doesn't leave behind a
    # session with no question to answer.
    first_question = generate_question(job_role, request.difficulty)

    session = InterviewSession(
        user_id=current_user.id,
        job_role=job_role,
        difficulty=request.difficulty,
        current_question=first_question,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "job_role": session.job_role,
        "difficulty": session.difficulty,
        "question_number": 1,
        "total_questions": MAX_QUESTIONS,
        "question": first_question
    }

@router.post("/answer")
def submit_answer(
    request: SubmitAnswer,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == request.session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Interview already completed")

    current_question = session.current_question
    if not current_question:
        raise HTTPException(
            status_code=409,
            detail="This session has no pending question. Please start a new interview."
        )

    evaluation = evaluate_answer(current_question, request.answer, session.job_role)

    is_complete = session.questions_asked + 1 >= MAX_QUESTIONS

    # Generate the follow-up before committing so that a failed generation
    # rolls the whole turn back and the candidate can simply resubmit, rather
    # than banking the answer and leaving a stale question pending.
    next_question = None
    if not is_complete:
        asked_questions = [
            a.question for a in db.query(InterviewAnswer).filter(
                InterviewAnswer.session_id == session.id
            ).all()
        ] + [current_question]
        next_question = generate_question(
            session.job_role,
            session.difficulty,
            asked_questions
        )

    answer_record = InterviewAnswer(
        session_id=session.id,
        question=current_question,
        answer=request.answer,
        score=evaluation.get("score", 0),
        ai_feedback=evaluation.get("feedback", ""),
        dimensions=evaluation.get("dimensions"),
        strengths=evaluation.get("strengths", ""),
        improvements=evaluation.get("improvements", ""),
    )
    db.add(answer_record)

    session.questions_asked += 1
    session.total_score += evaluation.get("score", 0)
    session.current_question = next_question

    if is_complete:
        session.status = "completed"

    db.commit()

    if is_complete:
        avg_score = round(session.total_score / session.questions_asked, 1)
        all_answers = db.query(InterviewAnswer).filter(
            InterviewAnswer.session_id == session.id
        ).order_by(InterviewAnswer.created_at).all()
        return {
            "status": "completed",
            "score": evaluation.get("score", 0),
            "feedback": evaluation.get("feedback", ""),
            "strengths": evaluation.get("strengths", ""),
            "improvements": evaluation.get("improvements", ""),
            "session_complete": True,
            "total_score": session.total_score,
            "average_score": avg_score,
            "questions_asked": session.questions_asked,
            "next_question": None,
            # Full breakdown so the completion screen needs no second request.
            "analytics": build_session_analytics(session, all_answers),
        }

    return {
        "status": "ongoing",
        "score": evaluation.get("score", 0),
        "feedback": evaluation.get("feedback", ""),
        "strengths": evaluation.get("strengths", ""),
        "improvements": evaluation.get("improvements", ""),
        "session_complete": False,
        "question_number": session.questions_asked + 1,
        "total_questions": MAX_QUESTIONS,
        "next_question": next_question
    }

@router.get("/sessions/{session_id}/analytics", response_model=InterviewAnalyticsOut)
def get_session_analytics(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dimension breakdown, strengths, weaknesses and practice suggestions."""
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    answers = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == session.id
    ).order_by(InterviewAnswer.created_at).all()

    return build_session_analytics(session, answers)


@router.get("/sessions", response_model=list[SessionOut])
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).order_by(InterviewSession.created_at.desc()).all()

@router.get("/sessions/{session_id}/answers", response_model=list[AnswerOut])
def get_answers(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == session_id
    ).all()