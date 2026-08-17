import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from app.models.github import GitHubProfile
from app.models.user import User
from app.routers.users import get_current_user
from app.schemas.github import GitHubConnect, GitHubOut, GitHubAnalysisOut
from app.services.github_analyzer import (
    GitHubNotFound,
    GitHubRateLimited,
    GitHubUnavailable,
    fetch_github_data,
)
from app.services.github_insights import analyze_profile

router = APIRouter(prefix="/api/github", tags=["GitHub"])

# Unauthenticated GitHub allows only 60 requests/hour and each sync costs two,
# so a re-sync inside this window returns the stored profile instead.
CACHE_MINUTES = int(os.getenv("GITHUB_CACHE_MINUTES", "60"))

# Only the top repos are returned to the client; the full list is kept in the
# row so insights can be recomputed without another API call.
REPOS_IN_RESPONSE = 10


def _profile_payload(profile: GitHubProfile, cached: bool) -> dict:
    repos = profile.repos or []
    return {
        "id": profile.id,
        "github_username": profile.github_username,
        "repo_count": profile.repo_count,
        "total_stars": profile.total_stars,
        "top_languages": profile.top_languages or [],
        "repos": repos[:REPOS_IN_RESPONSE],
        "developer_score": profile.developer_score,
        "followers": profile.followers,
        "following": profile.following,
        "synced_at": profile.synced_at,
        "cached": cached,
        "insights": analyze_profile({
            "repos": repos,
            "repo_count": profile.repo_count,
            "total_stars": profile.total_stars,
            "followers": profile.followers,
            "top_languages": profile.top_languages or [],
        }),
    }


def _is_fresh(profile: GitHubProfile, username: str) -> bool:
    if not profile or not profile.synced_at:
        return False
    if profile.github_username.lower() != username.lower():
        return False
    return datetime.utcnow() - profile.synced_at < timedelta(minutes=CACHE_MINUTES)


@router.post("/connect", response_model=GitHubAnalysisOut)
def connect_github(
    request: GitHubConnect,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    username = request.github_username.strip().lstrip("@")
    if not username:
        raise HTTPException(status_code=400, detail="Enter a GitHub username")

    existing = db.query(GitHubProfile).filter(
        GitHubProfile.user_id == current_user.id
    ).first()

    # Serve the stored profile rather than spending rate limit on data we
    # already have, unless the user explicitly asked for a refresh.
    if not request.force and _is_fresh(existing, username):
        return _profile_payload(existing, cached=True)

    try:
        data = fetch_github_data(username)
    except GitHubNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except GitHubRateLimited as exc:
        headers = {}
        if exc.reset_at:
            retry_after = max(1, int((exc.reset_at - datetime.now(exc.reset_at.tzinfo)).total_seconds()))
            headers["Retry-After"] = str(retry_after)
        # 429 rather than GitHub's 403, so the client can distinguish "wait"
        # from "forbidden". Stale data beats no data, so say what we still have.
        detail = str(exc)
        if existing:
            detail += (
                f" Showing your profile as of "
                f"{existing.synced_at:%d %b %H:%M} in the meantime."
            )
        raise HTTPException(status_code=429, detail=detail, headers=headers)
    except GitHubUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    profile = existing or GitHubProfile(user_id=current_user.id)
    profile.github_username = data["github_username"]
    profile.repo_count = data["repo_count"]
    profile.total_stars = data["total_stars"]
    profile.top_languages = data["top_languages"]
    profile.repos = data["repos"]
    profile.developer_score = data["developer_score"]
    profile.followers = data["followers"]
    profile.following = data["following"]
    profile.synced_at = datetime.utcnow()

    if not existing:
        db.add(profile)
    db.commit()
    db.refresh(profile)

    return _profile_payload(profile, cached=False)


@router.get("/profile", response_model=GitHubAnalysisOut)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(GitHubProfile).filter(
        GitHubProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No GitHub profile connected")
    # Always served from storage — reading your own profile never costs quota.
    return _profile_payload(profile, cached=True)
