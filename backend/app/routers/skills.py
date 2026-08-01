from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from app.models.skill_gap import SkillGap
from app.models.resume import Resume
from app.schemas.skill_gap import SkillGapRequest, SkillGapOut
from app.routers.users import get_current_user
from app.models.user import User
from app.services.skill_gap_engine import analyze_skill_gap

router = APIRouter(prefix="/api/skills", tags=["Skills"])

@router.post("/analyze", response_model=SkillGapOut, status_code=201)
def analyze_gap(
    request: SkillGapRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(
        Resume.id == request.resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.parsed_text:
        raise HTTPException(status_code=400, detail="Resume has no parsed text")

    result = analyze_skill_gap(resume.parsed_text, request.job_description)

    gap = SkillGap(
        user_id=current_user.id,
        resume_id=resume.id,
        job_title=request.job_title,
        job_description=request.job_description,
        matched_skills=result["matched_skills"],
        missing_skills=result["missing_skills"],
        match_score=result["match_score"]
    )
    db.add(gap)
    db.commit()
    db.refresh(gap)
    return gap

@router.get("/gaps/{resume_id}", response_model=list[SkillGapOut])
def get_gaps(
    resume_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    gaps = db.query(SkillGap).filter(
        SkillGap.resume_id == resume_id,
        SkillGap.user_id == current_user.id
    ).all()
    return gaps