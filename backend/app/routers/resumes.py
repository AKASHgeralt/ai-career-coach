from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from app.models.resume import Resume
from app.schemas.resume import ResumeOut, ResumeDetail
from app.routers.users import get_current_user
from app.models.user import User
from app.services.nlp import analyze_resume

import fitz  # PyMuPDF
import os
import uuid

router = APIRouter(
    prefix="/api/resumes",
    tags=["Resumes"]
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""

    for page in doc:
        text += page.get_text()

    doc.close()
    return text.strip()


def calculate_ats_score(text: str) -> int:
    score = 0

    keywords = [
        "experience",
        "skills",
        "education",
        "project",
        "python",
        "java",
        "javascript",
        "sql",
        "api",
        "machine learning",
        "react",
        "docker",
        "aws",
        "leadership",
        "communication",
        "team",
        "github"
    ]

    text_lower = text.lower()

    for keyword in keywords:
        if keyword in text_lower:
            score += 5

    if len(text) > 500:
        score += 10

    if len(text) > 1000:
        score += 10

    return min(score, 100)


@router.post("/upload", response_model=ResumeOut, status_code=201)
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files allowed"
        )

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")

    with open(file_path, "wb") as f:
        content = file.file.read()
        f.write(content)

    parsed_text = extract_text_from_pdf(file_path)
    ats_score = calculate_ats_score(parsed_text)

    resume = Resume(
        user_id=current_user.id,
        file_name=file.filename,
        file_path=file_path,
        parsed_text=parsed_text,
        ats_score=ats_score
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
    ).all()


@router.get("/{resume_id}", response_model=ResumeDetail)
def get_resume(
    resume_id: str,
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
    resume_id: str,
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

    if os.path.exists(resume.file_path):
        os.remove(resume.file_path)

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
    resume_id: str,
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