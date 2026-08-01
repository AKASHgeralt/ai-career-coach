from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from app.models.interview import InterviewSession, InterviewAnswer
from app.schemas.interview import StartInterview, SubmitAnswer, SessionOut, AnswerOut
from app.routers.users import get_current_user
from app.models.user import User
from app.services.interview_engine import generate_question, evaluate_answer

router = APIRouter(prefix="/api/interview", tags=["Interview"])

MAX_QUESTIONS = 5

@router.post("/start")
def start_interview(
    request: StartInterview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = InterviewSession(
        user_id=current_user.id,
        job_role=request.job_role,
        difficulty=request.difficulty,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    first_question = generate_question(request.job_role, request.difficulty)

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

    previous_answers = db.query(InterviewAnswer).filter(
        InterviewAnswer.session_id == session.id
    ).all()
    previous_questions = [a.question for a in previous_answers]

    current_question = generate_question(
        session.job_role,
        session.difficulty,
        previous_questions
    ) if not previous_answers else previous_answers[-1].question

    if previous_answers:
        current_question = previous_answers[-1].question

    evaluation = evaluate_answer(current_question, request.answer, session.job_role)

    answer_record = InterviewAnswer(
        session_id=session.id,
        question=current_question,
        answer=request.answer,
        score=evaluation.get("score", 0),
        ai_feedback=evaluation.get("feedback", "")
    )
    db.add(answer_record)

    session.questions_asked += 1
    session.total_score += evaluation.get("score", 0)

    is_complete = session.questions_asked >= MAX_QUESTIONS

    if is_complete:
        session.status = "completed"

    db.commit()

    if is_complete:
        avg_score = round(session.total_score / session.questions_asked, 1)
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
            "next_question": None
        }

    next_question = generate_question(
        session.job_role,
        session.difficulty,
        previous_questions + [current_question]
    )

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
    session_id: str,
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