from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from app.models.resume import Resume
from app.models.skill_gap import SkillGap
from app.models.recommendation import Recommendation
from app.models.roadmap_task import RoadmapTask
from app.schemas.resume import ResumeOut, ResumeDetail
from app.routers.users import get_current_user
from app.models.user import User
from app.services.nlp import analyze_resume, calculate_smart_ats_score, extract_skills
from app.services.roles import role_match_title
from app.services.skill_gap_engine import skills_for_role
from app.services.resume_versions import (
    build_version_history, compare_resumes, next_version_for,
)
from app.schemas.resume import ResumeVersionHistory, ResumeComparison

import fitz  # PyMuPDF
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/resumes",
    tags=["Resumes"]
)

# Matches the 5MB the upload UI promises. Enforced server-side because the
# client-side check is trivially bypassed.
MAX_RESUME_BYTES = 5 * 1024 * 1024
PDF_MAGIC = b"%PDF-"
MAX_FILENAME_LEN = 120


def sanitize_filename(name: str | None) -> str:
    """Reduce a client-supplied filename to something safe to store and render.

    The file on disk is always a server-generated UUID, so this is about the
    name we persist and echo back: strip any directory components, drop control
    characters, and bound the length.
    """
    if not name:
        return "resume.pdf"
    # basename twice to cover both separator styles regardless of host OS
    base = os.path.basename(name.replace("\\", "/")).strip()
    cleaned = "".join(ch for ch in base if ch.isprintable() and ch not in '<>:"|?*')
    cleaned = cleaned.strip(". ") or "resume.pdf"
    if len(cleaned) > MAX_FILENAME_LEN:
        stem, ext = os.path.splitext(cleaned)
        cleaned = stem[:MAX_FILENAME_LEN - len(ext)] + ext
    return cleaned


def read_upload_within_limit(file: UploadFile) -> bytes:
    """Read an upload, refusing anything over the size cap.

    Reads one byte past the limit so an oversized file is rejected without
    buffering the whole thing.
    """
    content = file.file.read(MAX_RESUME_BYTES + 1)
    if len(content) > MAX_RESUME_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Resume must be under {MAX_RESUME_BYTES // (1024 * 1024)}MB",
        )
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if not content.startswith(PDF_MAGIC):
        # Content-based, so renaming a .docx to .pdf doesn't get through.
        raise HTTPException(
            status_code=400,
            detail="File is not a valid PDF",
        )
    return content


def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF bytes, turning parser failures into a 400.

    Parsing from memory rather than from a path means a malformed PDF never
    leaves a file on disk to clean up, and no OS file handle can linger and
    block deletion. A corrupt or password-protected PDF is bad input, not a
    server fault, and the underlying PyMuPDF error must not reach the client.
    """
    try:
        with fitz.open(stream=content, filetype="pdf") as doc:
            if doc.needs_pass:
                raise HTTPException(
                    status_code=400,
                    detail="This PDF is password protected. Please upload an unlocked copy.",
                )
            return "".join(page.get_text() for page in doc).strip()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read this PDF. It may be corrupt or in an unsupported format.",
        )


@router.post("/upload", response_model=ResumeOut, status_code=201)
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content = read_upload_within_limit(file)
    safe_name = sanitize_filename(file.filename)

    # Validate and parse before anything touches the filesystem, so a bad
    # upload never creates a file that needs cleaning up.
    parsed_text = extract_text_from_pdf(content)
    # Same scorer the analyse endpoint and version comparison use, so a
    # resume's score is consistent everywhere it appears. The upload path
    # previously used a separate keyword-count scorer, which made the
    # version history disagree with the analysis view.
    ats_score = calculate_smart_ats_score(parsed_text, extract_skills(parsed_text))

    existing_versions = [
        v for (v,) in
        db.query(Resume.version).filter(Resume.user_id == current_user.id).all()
    ]
    version = next_version_for(existing_versions)

    # The PDF bytes are not persisted. extract_text_from_pdf has already pulled
    # everything the app uses out of them, and no endpoint ever served the file
    # back, so writing it only created orphan-cleanup paths and a dependency on
    # a writable disk that the free hosting tiers do not provide.
    resume = Resume(
        user_id=current_user.id,
        file_name=safe_name,
        parsed_text=parsed_text,
        ats_score=ats_score,
        version=version,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return resume


@router.get("", response_model=list[ResumeOut])
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Resume).filter(
        Resume.user_id == current_user.id
    ).order_by(Resume.version.desc()).all()


@router.get("/versions", response_model=ResumeVersionHistory)
def get_version_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Every version with its ATS score, for the improvement chart."""
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).all()
    return build_version_history(resumes)


@router.get("/compare", response_model=ResumeComparison)
def compare_versions(
    base: UUID,
    target: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare two of your resume versions.

    Arguments are ordered automatically, so the older version is always the
    baseline regardless of which way round they were passed.
    """
    if base == target:
        raise HTTPException(status_code=400, detail="Pick two different versions to compare")

    rows = db.query(Resume).filter(
        Resume.id.in_([base, target]),
        Resume.user_id == current_user.id,
    ).all()
    if len(rows) != 2:
        raise HTTPException(status_code=404, detail="One or both resumes were not found")

    older, newer = sorted(rows, key=lambda r: (r.version, r.uploaded_at))
    role_skills = skills_for_role(role_match_title(current_user.target_role))
    return compare_resumes(older, newer, role_skills)


@router.get("/{resume_id}", response_model=ResumeDetail)
def get_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    return resume


@router.delete("/{resume_id}")
def delete_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    gap_ids = [
        gap_id for (gap_id,) in
        db.query(SkillGap.id).filter(SkillGap.resume_id == resume.id).all()
    ]
    if gap_ids:
        rec_ids = [
            rec_id for (rec_id,) in
            db.query(Recommendation.id).filter(Recommendation.gap_id.in_(gap_ids)).all()
        ]
        if rec_ids:
            # Tasks reference recommendations, so they must go first or the
            # foreign key blocks the delete.
            db.query(RoadmapTask).filter(
                RoadmapTask.recommendation_id.in_(rec_ids)
            ).delete(synchronize_session=False)
        db.query(Recommendation).filter(Recommendation.gap_id.in_(gap_ids)).delete(synchronize_session=False)
        db.query(SkillGap).filter(SkillGap.resume_id == resume.id).delete(synchronize_session=False)

    db.delete(resume)
    db.commit()

    return {
        "message": "Resume deleted"
    }


# -----------------------------
# AI Resume Analysis Endpoint
# -----------------------------
@router.get("/{resume_id}/analyze")
def analyze_resume_endpoint(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    if not resume.parsed_text:
        raise HTTPException(
            status_code=400,
            detail="Resume text not available"
        )

    analysis = analyze_resume(resume.parsed_text)

    # Save updated ATS score
    resume.ats_score = analysis["ats_score"]
    db.commit()

    return {
        "resume_id": resume.id,
        "file_name": resume.file_name,
        **analysis
    }