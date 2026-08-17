from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from app.routers.users import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.models.skill_gap import SkillGap
from app.models.interview import InterviewSession
from app.models.github import GitHubProfile
from app.models.recommendation import Recommendation
from app.services.roles import role_label
from app.services.readiness_data import build_readiness
from app.services.timeline import DEFAULT_LIMIT, build_progress_series, build_timeline
from app.schemas.readiness import ReadinessOut
from app.schemas.timeline import TimelineOut
from collections import Counter

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/timeline", response_model=TimelineOut)
def get_timeline(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Career events in reverse-chronological order, plus per-signal series.

    Built from real recorded timestamps only — no back-filled history.
    """
    events = build_timeline(db, current_user, limit=limit)
    return {"events": events, "series": build_progress_series(events)}


@router.get("/readiness", response_model=ReadinessOut)
def get_readiness(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Career Readiness Score with a full, explainable component breakdown."""
    return build_readiness(db, current_user)

@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Resume stats
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).all()
    resume_count = len(resumes)
    avg_ats = round(sum(r.ats_score for r in resumes) / resume_count, 1) if resume_count else 0

    # Skill gap stats
    gaps = db.query(SkillGap).filter(SkillGap.user_id == current_user.id).all()
    all_missing = []
    for gap in gaps:
        if gap.missing_skills:
            all_missing.extend(gap.missing_skills)
    top_missing = [{"skill": s, "count": c} for s, c in Counter(all_missing).most_common(5)]
    avg_match = round(sum(g.match_score for g in gaps) / len(gaps), 1) if gaps else 0

    # Interview stats
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).all()
    interviews_count = len(sessions)
    completed = [s for s in sessions if s.status == "completed"]
    avg_interview_score = 0
    if completed:
        avg_interview_score = round(
            sum(s.total_score / max(s.questions_asked, 1) for s in completed) / len(completed), 1
        )

    # GitHub stats
    github = db.query(GitHubProfile).filter(
        GitHubProfile.user_id == current_user.id
    ).first()

    # Recent activity
    recent_resumes = sorted(resumes, key=lambda r: r.uploaded_at, reverse=True)[:3]
    recent_gaps = sorted(gaps, key=lambda g: g.created_at, reverse=True)[:3]
    recent_sessions = sorted(sessions, key=lambda s: s.created_at, reverse=True)[:3]

    return {
        "user": {
            "full_name": current_user.full_name,
            "email": current_user.email,
            "avatar_url": current_user.avatar_url,
            "target_role": current_user.target_role,
            "target_role_label": role_label(current_user.target_role),
        },
        "resumes": {
            "count": resume_count,
            "avg_ats_score": avg_ats,
            "recent": [
                {
                    "id": str(r.id),
                    "file_name": r.file_name,
                    "ats_score": r.ats_score,
                    "uploaded_at": r.uploaded_at.isoformat()
                } for r in recent_resumes
            ]
        },
        "skill_gaps": {
            "total_analyses": len(gaps),
            "avg_match_score": avg_match,
            "top_missing_skills": top_missing,
            "recent": [
                {
                    "id": str(g.id),
                    "job_title": g.job_title,
                    "match_score": g.match_score,
                    "created_at": g.created_at.isoformat()
                } for g in recent_gaps
            ]
        },
        "interviews": {
            "total_sessions": interviews_count,
            "completed_sessions": len(completed),
            "avg_score": avg_interview_score,
            "recent": [
                {
                    "id": str(s.id),
                    "job_role": s.job_role,
                    "total_score": s.total_score,
                    "status": s.status,
                    "created_at": s.created_at.isoformat()
                } for s in recent_sessions
            ]
        },
        "github": {
            "connected": github is not None,
            "username": github.github_username if github else None,
            "developer_score": github.developer_score if github else 0,
            "repo_count": github.repo_count if github else 0,
            "total_stars": github.total_stars if github else 0,
            "top_languages": github.top_languages if github else []
        }
    }