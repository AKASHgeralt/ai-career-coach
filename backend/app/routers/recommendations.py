from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from app.models.recommendation import Recommendation
from app.models.skill_gap import SkillGap
from app.schemas.recommendation import RoadmapRequest, RecommendationOut
from app.routers.users import get_current_user
from app.models.user import User
from app.services.recommendation_engine import get_recommendations
from app.services.llm import LLMError
from app.models.roadmap_task import RoadmapTask
from app.schemas.roadmap_task import (
    RoadmapTasksOut, RoadmapTaskUpdate, RoadmapTaskOut,
)
from app.services.roadmap_tasks import (
    replace_tasks_for_recommendation, progress_for, set_completed,
)

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


def _ordered_tasks(db: Session, recommendation_id) -> list[RoadmapTask]:
    return (
        db.query(RoadmapTask)
        .filter(RoadmapTask.recommendation_id == recommendation_id)
        .order_by(RoadmapTask.week, RoadmapTask.position)
        .all()
    )

@router.post("/roadmap", response_model=RecommendationOut, status_code=201)
def generate_roadmap(
    request: RoadmapRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    gap = db.query(SkillGap).filter(
        SkillGap.id == request.gap_id,
        SkillGap.user_id == current_user.id
    ).first()
    if not gap:
        raise HTTPException(status_code=404, detail="Skill gap analysis not found")

    result = get_recommendations(gap.missing_skills, request.target_role)

    recommendation = Recommendation(
        user_id=current_user.id,
        gap_id=gap.id,
        courses=result.get("courses", []),
        projects=result.get("projects", []),
        books=result.get("books", []),
        roadmap=result.get("roadmap", [])
    )
    db.add(recommendation)
    db.flush()  # need the id before materialising its tasks

    replace_tasks_for_recommendation(db, recommendation, recommendation.roadmap)

    db.commit()
    db.refresh(recommendation)
    return recommendation


@router.get("/{gap_id}/tasks", response_model=RoadmapTasksOut)
def get_roadmap_tasks(
    gap_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rec = db.query(Recommendation).filter(
        Recommendation.gap_id == gap_id,
        Recommendation.user_id == current_user.id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="No roadmap found for this gap")

    tasks = _ordered_tasks(db, rec.id)

    # Roadmaps generated before task tracking existed have no rows yet.
    # Backfill on first read so old roadmaps become checkable too.
    if not tasks and rec.roadmap:
        replace_tasks_for_recommendation(db, rec, rec.roadmap)
        db.commit()
        tasks = _ordered_tasks(db, rec.id)

    return {
        "recommendation_id": rec.id,
        "gap_id": rec.gap_id,
        "progress": progress_for(tasks),
        "tasks": tasks,
    }


@router.patch("/tasks/{task_id}", response_model=RoadmapTaskOut)
def update_roadmap_task(
    task_id: UUID,
    payload: RoadmapTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(RoadmapTask).filter(
        RoadmapTask.id == task_id,
        RoadmapTask.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return set_completed(db, task, payload.completed)

@router.get("/{gap_id}", response_model=RecommendationOut)
def get_recommendation(
    gap_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rec = db.query(Recommendation).filter(
        Recommendation.gap_id == gap_id,
        Recommendation.user_id == current_user.id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="No recommendations found for this gap")
    return rec