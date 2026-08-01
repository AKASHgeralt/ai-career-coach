from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from app.models.recommendation import Recommendation
from app.models.skill_gap import SkillGap
from app.schemas.recommendation import RoadmapRequest, RecommendationOut
from app.routers.users import get_current_user
from app.models.user import User
from app.services.recommendation_engine import get_recommendations

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])

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
    db.commit()
    db.refresh(recommendation)
    return recommendation

@router.get("/{gap_id}", response_model=RecommendationOut)
def get_recommendation(
    gap_id: str,
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