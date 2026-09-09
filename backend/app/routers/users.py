from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
from jose import JWTError
from fastapi.security import OAuth2PasswordBearer
from database import get_db
from app.models.user import User
from app.schemas.user import UserOut, TargetRoleOption, TargetRoleUpdate
from app.services.auth import decode_token
from app.services.roles import TARGET_ROLES

from datetime import datetime
import hashlib
import uuid
from uuid import UUID

router = APIRouter(prefix="/api/users", tags=["Users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

MAX_AVATAR_SIZE = 3 * 1024 * 1024  # 3MB

AVATAR_MIME = {"png": "image/png", "jpg": "image/jpeg",
               "gif": "image/gif", "webp": "image/webp"}

# Detected from file content, not the client-supplied filename/content-type,
# so a renamed non-image file can't slip through.
def _detect_image_extension(header: bytes) -> str | None:
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    return None

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/target-roles", response_model=list[TargetRoleOption])
def list_target_roles():
    """Catalogue of selectable roles, so the client never hardcodes the list."""
    return TARGET_ROLES

@router.put("/me/target-role", response_model=UserOut)
def set_target_role(
    payload: TargetRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.target_role = payload.target_role
    current_user.target_role_updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/me/avatar", response_model=UserOut)
def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content = file.file.read(MAX_AVATAR_SIZE + 1)
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="Image must be under 3MB")

    ext = _detect_image_extension(content[:16])
    if not ext:
        raise HTTPException(status_code=400, detail="File must be a PNG, JPEG, GIF or WEBP image")

    current_user.avatar_data = content
    current_user.avatar_mime = AVATAR_MIME[ext]
    # The digest makes the URL change whenever the image does, so a cached copy
    # of the previous avatar is never shown after an upload.
    tag = hashlib.sha256(content).hexdigest()[:16]
    current_user.avatar_url = f"/api/users/{current_user.id}/avatar?v={tag}"
    db.commit()
    db.refresh(current_user)

    return current_user

@router.delete("/me/avatar", response_model=UserOut)
def remove_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.avatar_url:
        current_user.avatar_url = None
        current_user.avatar_data = None
        current_user.avatar_mime = None
        db.commit()
        db.refresh(current_user)
    return current_user

@router.get("/{user_id}/avatar")
def get_avatar(user_id: UUID, db: Session = Depends(get_db)):
    """Serve avatar bytes for an <img> tag.

    Deliberately unauthenticated: a browser image request cannot carry the bearer
    token, and this replaces a StaticFiles mount that was equally open. The route
    exposes nothing but the picture, and only to someone who already has the
    account's UUID, which is never shown to other users.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.avatar_data:
        raise HTTPException(status_code=404, detail="No avatar set")
    return Response(
        content=user.avatar_data,
        media_type=user.avatar_mime or "application/octet-stream",
        # The URL carries a content digest, so a cached copy can never be stale.
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
