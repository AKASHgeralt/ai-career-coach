from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class GitHubConnect(BaseModel):
    github_username: str
    # Bypass the cache window and re-fetch from GitHub. Defaults false so the
    # common path doesn't spend rate limit.
    force: bool = False

class GitHubOut(BaseModel):
    id: UUID
    github_username: str
    repo_count: int
    total_stars: int
    top_languages: list
    developer_score: float
    followers: int
    following: int
    synced_at: datetime

    class Config:
        from_attributes = True

class GitHubInsightStats(BaseModel):
    repos_with_description: int
    repos_without_description: int
    repos_with_stars: int
    stale_repos: int
    language_count: int

class GitHubInsights(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    actions: list[str]
    stats: GitHubInsightStats

class GitHubAnalysisOut(GitHubOut):
    repos: list = []
    # True when served from storage rather than a fresh GitHub call.
    cached: bool = False
    insights: GitHubInsights
