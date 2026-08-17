"""Career progress timeline, assembled from real recorded events.

Every entry corresponds to a row that actually exists with a real timestamp —
a resume upload, a skill gap analysis, an interview session, a GitHub sync, a
completed roadmap task. Nothing is back-filled or interpolated.

Note on what is deliberately absent: there is no historical readiness score.
Readiness is computed live from current data and has never been snapshotted, so
plotting it over time would mean inventing values. The individual measurements
that feed it are real and are plotted instead.
"""
from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.skill_gap import SkillGap
from app.models.interview import InterviewSession
from app.models.github import GitHubProfile
from app.models.roadmap_task import RoadmapTask

# Event kinds, aligned with the readiness signal each one moves.
KIND_RESUME = "resume"
KIND_SKILLS = "skills"
KIND_INTERVIEW = "interview"
KIND_GITHUB = "github"
KIND_TASK = "task"

DEFAULT_LIMIT = 40


def _event(kind, at, title, detail=None, metric_label=None, metric_value=None):
    return {
        "kind": kind,
        "at": at,
        "title": title,
        "detail": detail,
        "metric_label": metric_label,
        "metric_value": metric_value,
    }


def build_timeline(db: Session, user, limit: int = DEFAULT_LIMIT) -> list[dict]:
    """Every recorded career event for a user, newest first."""
    events: list[dict] = []

    for r in db.query(Resume).filter(Resume.user_id == user.id).all():
        if r.uploaded_at:
            events.append(_event(
                KIND_RESUME, r.uploaded_at,
                "Resume uploaded", r.file_name,
                "ATS", float(r.ats_score or 0),
            ))

    for g in db.query(SkillGap).filter(SkillGap.user_id == user.id).all():
        if g.created_at:
            missing = len(g.missing_skills or [])
            events.append(_event(
                KIND_SKILLS, g.created_at,
                "Skill gap analysed", g.job_title or "Untitled role",
                "Match", float(g.match_score or 0),
            ))
            events[-1]["detail"] = (
                f"{g.job_title or 'Untitled role'} — {missing} skill"
                f"{'s' if missing != 1 else ''} missing"
            )

    for s in db.query(InterviewSession).filter(
        InterviewSession.user_id == user.id,
        InterviewSession.questions_asked > 0,
    ).all():
        if s.created_at:
            # Per-question average rescaled to 0-100, matching the readiness signal.
            avg = (s.total_score / s.questions_asked) * 10
            events.append(_event(
                KIND_INTERVIEW, s.created_at,
                "Mock interview",
                f"{s.job_role} — {s.questions_asked} question"
                f"{'s' if s.questions_asked != 1 else ''} answered",
                "Score", round(avg, 1),
            ))

    gh = db.query(GitHubProfile).filter(GitHubProfile.user_id == user.id).first()
    if gh and gh.synced_at:
        events.append(_event(
            KIND_GITHUB, gh.synced_at,
            "GitHub synchronised", f"@{gh.github_username}",
            "Developer score", float(gh.developer_score or 0),
        ))

    for t in db.query(RoadmapTask).filter(
        RoadmapTask.user_id == user.id,
        RoadmapTask.completed.is_(True),
    ).all():
        if t.completed_at:
            events.append(_event(
                KIND_TASK, t.completed_at,
                "Roadmap task completed", f"Week {t.week} — {t.title}",
            ))

    events.sort(key=lambda e: e["at"], reverse=True)
    return events[:limit]


def build_progress_series(timeline: list[dict]) -> dict:
    """Chronological series per measurable signal, for charting.

    Only signals with at least two data points are returned — a single point
    is not a trend and drawing it as one would overstate what's known.
    """
    series: dict[str, list] = {}
    for event in sorted(timeline, key=lambda e: e["at"]):
        if event["metric_value"] is None:
            continue
        series.setdefault(event["kind"], []).append({
            "at": event["at"],
            "value": event["metric_value"],
            "label": event["metric_label"],
        })

    return {kind: points for kind, points in series.items() if len(points) >= 2}
