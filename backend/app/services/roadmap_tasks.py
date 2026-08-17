"""Turns a generated roadmap into checkable, persisted tasks.

The LLM returns a roadmap as JSON. Rather than tracking completion inside that
blob, we materialise one row per task so progress is relational — countable in
SQL, and safe to update without rewriting the whole roadmap.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.roadmap_task import RoadmapTask

# Guards against a malformed LLM response creating an unbounded number of rows.
MAX_WEEKS = 26
MAX_TASKS_PER_WEEK = 12


def _coerce_week(value, fallback: int) -> int:
    try:
        week = int(value)
    except (TypeError, ValueError):
        return fallback
    return week if 1 <= week <= MAX_WEEKS else fallback


def build_tasks_from_roadmap(roadmap: list, user_id, recommendation_id) -> list[RoadmapTask]:
    """Create (unsaved) RoadmapTask rows from roadmap JSON.

    Prefers each week's explicit `tasks` list. Older roadmaps generated before
    tasks existed have no such list, so the week's focus becomes a single task
    and those roadmaps stay usable.
    """
    rows: list[RoadmapTask] = []
    if not isinstance(roadmap, list):
        return rows

    for index, week_entry in enumerate(roadmap[:MAX_WEEKS], start=1):
        if not isinstance(week_entry, dict):
            continue

        week = _coerce_week(week_entry.get("week"), index)
        focus = str(week_entry.get("focus") or f"Week {week}").strip()
        goal = str(week_entry.get("goal") or "").strip() or None

        raw_tasks = week_entry.get("tasks")
        titles = []
        if isinstance(raw_tasks, list):
            titles = [
                str(t).strip() for t in raw_tasks[:MAX_TASKS_PER_WEEK]
                if str(t).strip()
            ]

        if not titles:
            # Fallback: the week itself becomes the unit of work.
            titles = [focus]

        for position, title in enumerate(titles):
            rows.append(RoadmapTask(
                user_id=user_id,
                recommendation_id=recommendation_id,
                week=week,
                title=title[:500],
                detail=goal,
                position=position,
                # Set explicitly: the column default only applies at INSERT, so
                # without this the in-memory object reads None before flush.
                completed=False,
            ))

    return rows


def replace_tasks_for_recommendation(
    db: Session, recommendation, roadmap: list
) -> list[RoadmapTask]:
    """Regenerate the task list for a recommendation, discarding any old one.

    Called when a roadmap is (re)generated. Existing completion state for that
    recommendation is intentionally dropped, because the tasks it referred to
    no longer exist.
    """
    db.query(RoadmapTask).filter(
        RoadmapTask.recommendation_id == recommendation.id
    ).delete(synchronize_session=False)

    rows = build_tasks_from_roadmap(roadmap, recommendation.user_id, recommendation.id)
    for row in rows:
        db.add(row)
    return rows


def progress_for(tasks: list) -> dict:
    """Completion summary for a task list."""
    total = len(tasks)
    done = sum(1 for t in tasks if t.completed)
    return {
        "total": total,
        "completed": done,
        "percent": round(done / total * 100, 1) if total else 0.0,
    }


def set_completed(db: Session, task: RoadmapTask, completed: bool) -> RoadmapTask:
    task.completed = completed
    task.completed_at = datetime.utcnow() if completed else None
    db.commit()
    db.refresh(task)
    return task
