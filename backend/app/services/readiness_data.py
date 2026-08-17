"""Gathers the four readiness signals for a user out of the database.

Kept separate from readiness.py so the scoring maths stays a pure function that
can be tested without a database.
"""
from collections import Counter

from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.skill_gap import SkillGap
from app.models.interview import InterviewSession
from app.models.github import GitHubProfile
from app.models.roadmap_task import RoadmapTask
from app.services.roadmap_tasks import progress_for
from app.services.readiness import compute_readiness
from app.services.next_action import determine_next_action
from app.services.roles import role_label


def _resume_signal(db: Session, user_id) -> tuple[float | None, str | None]:
    """Most recent resume's ATS score — current state, not a historical average."""
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == user_id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )
    if not resume:
        return None, None
    return float(resume.ats_score or 0), f"ATS score of your latest resume ({resume.file_name})."


def _skills_signal(db: Session, user_id, target_role) -> tuple[float | None, str | None]:
    """Match score of the most recent analysis, preferring one for the target role."""
    gaps = (
        db.query(SkillGap)
        .filter(SkillGap.user_id == user_id)
        .order_by(SkillGap.created_at.desc())
        .all()
    )
    if not gaps:
        return None, None

    label = role_label(target_role)
    chosen = None
    if label:
        chosen = next(
            (g for g in gaps if (g.job_title or "").strip().lower() == label.lower()),
            None,
        )
    scoped_to_role = chosen is not None
    chosen = chosen or gaps[0]

    detail = (
        f"Match against your target role from your most recent {chosen.job_title} analysis."
        if scoped_to_role
        else f"Most recent skill gap analysis ({chosen.job_title or 'untitled role'}). "
             "Run one against your target role for a more relevant score."
    )
    return float(chosen.match_score or 0), detail


def _interview_signal(db: Session, user_id) -> tuple[float | None, str | None]:
    """Mean score per answered question across sessions, rescaled 0-10 -> 0-100.

    Counts any session with at least one answer. Requiring completion would
    discard real measured performance from sessions a user abandoned.
    """
    sessions = (
        db.query(InterviewSession)
        .filter(
            InterviewSession.user_id == user_id,
            InterviewSession.questions_asked > 0,
        )
        .all()
    )
    if not sessions:
        return None, None

    per_session = [s.total_score / s.questions_asked for s in sessions]
    avg_out_of_10 = sum(per_session) / len(per_session)
    answered = sum(s.questions_asked for s in sessions)
    return (
        round(avg_out_of_10 * 10, 1),
        f"Average answer score across {answered} answered "
        f"question{'s' if answered != 1 else ''} in {len(sessions)} "
        f"session{'s' if len(sessions) != 1 else ''}.",
    )


def _github_signal(db: Session, user_id) -> tuple[float | None, str | None]:
    profile = (
        db.query(GitHubProfile).filter(GitHubProfile.user_id == user_id).first()
    )
    if not profile:
        return None, None
    return (
        float(profile.developer_score or 0),
        f"Developer score for @{profile.github_username}, from repositories, "
        "stars, language spread and followers.",
    )


def _skill_gap_context(db: Session, user_id, target_role) -> dict:
    """Facts the next-action engine needs about the user's skill gap history."""
    gaps = db.query(SkillGap).filter(SkillGap.user_id == user_id).all()
    label = role_label(target_role)

    role_scoped = [
        g for g in gaps
        if label and (g.job_title or "").strip().lower() == label.lower()
    ]
    # Prefer counting misses within target-role analyses; fall back to all of
    # them so the reason stays truthful about which set it counted.
    counted = role_scoped or gaps

    missing = Counter()
    for gap in counted:
        for skill in (gap.missing_skills or []):
            missing[skill] += 1

    top = missing.most_common(1)
    return {
        "top_missing_skill": (top[0][0], top[0][1]) if top else None,
        "gap_count": len(counted),
        "role_scoped_gap": bool(role_scoped),
        "top_missing_skills": [
            {"skill": s, "count": c} for s, c in missing.most_common(5)
        ],
    }


def _roadmap_progress(db: Session, user_id) -> dict:
    """Completion across every roadmap task the user has.

    Returned even when empty so the dashboard can show a truthful "no roadmap
    yet" state rather than an invented percentage.
    """
    tasks = db.query(RoadmapTask).filter(RoadmapTask.user_id == user_id).all()
    summary = progress_for(tasks)
    summary["has_roadmap"] = bool(tasks)
    return summary


def build_readiness(db: Session, user) -> dict:
    """Assemble every signal and compute the user's readiness score."""
    resume, resume_detail = _resume_signal(db, user.id)
    skills, skills_detail = _skills_signal(db, user.id, user.target_role)
    interview, interview_detail = _interview_signal(db, user.id)
    github, github_detail = _github_signal(db, user.id)

    result = compute_readiness(
        resume=resume,
        skills=skills,
        interview=interview,
        github=github,
        details={
            "resume": resume_detail,
            "skills": skills_detail,
            "interview": interview_detail,
            "github": github_detail,
        },
    )
    result["target_role"] = user.target_role
    result["target_role_label"] = role_label(user.target_role)

    context = _skill_gap_context(db, user.id, user.target_role)
    result["top_missing_skills"] = context["top_missing_skills"]
    result["roadmap_progress"] = _roadmap_progress(db, user.id)
    result["next_action"] = determine_next_action(
        readiness=result,
        target_role_label=result["target_role_label"],
        top_missing_skill=context["top_missing_skill"],
        gap_count=context["gap_count"],
        role_scoped_gap=context["role_scoped_gap"],
    )
    return result
