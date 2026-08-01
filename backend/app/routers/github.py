from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from app.models.github import GitHubProfile
from app.schemas.github import GitHubConnect, GitHubOut
from app.routers.users import get_current_user
from app.models.user import User
from app.services.github_analyzer import fetch_github_data

router = APIRouter(prefix="/api/github", tags=["GitHub"])

@router.post("/connect")
def connect_github(
    request: GitHubConnect,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        data = fetch_github_data(request.github_username)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    existing = db.query(GitHubProfile).filter(
        GitHubProfile.user_id == current_user.id
    ).first()

    if existing:
        existing.github_username = data["github_username"]
        existing.repo_count = data["repo_count"]
        existing.total_stars = data["total_stars"]
        existing.top_languages = data["top_languages"]
        existing.repos = data["repos"]
        existing.developer_score = data["developer_score"]
        existing.followers = data["followers"]
        existing.following = data["following"]
        from datetime import datetime
        existing.synced_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return {**data, "id": existing.id, "synced_at": existing.synced_at}

    profile = GitHubProfile(
        user_id=current_user.id,
        github_username=data["github_username"],
        repo_count=data["repo_count"],
        total_stars=data["total_stars"],
        top_languages=data["top_languages"],
        repos=data["repos"],
        developer_score=data["developer_score"],
        followers=data["followers"],
        following=data["following"],
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {**data, "id": profile.id, "synced_at": profile.synced_at}

@router.get("/profile", response_model=GitHubOut)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(GitHubProfile).filter(
        GitHubProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No GitHub profile connected")
    return profile