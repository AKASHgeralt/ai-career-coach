from pydantic import BaseModel, EmailStr, computed_field, field_validator
from uuid import UUID
from datetime import datetime

from app.services.roles import is_valid_role, role_label, VALID_ROLE_SLUGS

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: UUID
    full_name: str
    email: str
    avatar_url: str | None = None
    target_role: str | None = None
    target_role_updated_at: datetime | None = None
    created_at: datetime

    # Derived rather than stored, so the display name can never drift out of
    # sync with the slug that actually drives the analysis.
    @computed_field
    @property
    def target_role_label(self) -> str | None:
        return role_label(self.target_role)

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TargetRoleOption(BaseModel):
    slug: str
    label: str

class TargetRoleUpdate(BaseModel):
    target_role: str

    @field_validator("target_role")
    @classmethod
    def known_role(cls, v: str) -> str:
        if not is_valid_role(v):
            raise ValueError(
                f"Unknown target role '{v}'. Valid roles: {', '.join(VALID_ROLE_SLUGS)}"
            )
        return v
