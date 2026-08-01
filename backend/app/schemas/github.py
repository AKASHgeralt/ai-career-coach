from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class GitHubConnect(BaseModel):
    github_username: str

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