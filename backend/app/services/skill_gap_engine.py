from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from app.services.nlp import extract_skills, SKILLS_DB

model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_job_skills(job_description: str) -> list[str]:
    text_lower = job_description.lower()
    found = []
    for skill in SKILLS_DB:
        if skill in text_lower:
            found.append(skill)
    return list(set(found))

def compute_skill_gap(resume_skills: list[str], job_skills: list[str], threshold: float = 0.6) -> dict:
    if not resume_skills or not job_skills:
        return {
            "matched_skills": [],
            "missing_skills": job_skills,
            "match_score": 0.0
        }

    # Create embeddings
    resume_embeddings = model.encode(resume_skills, convert_to_numpy=True)
    job_embeddings = model.encode(job_skills, convert_to_numpy=True)

    # Normalize vectors for cosine similarity
    faiss.normalize_L2(resume_embeddings)
    faiss.normalize_L2(job_embeddings)

    # Build FAISS index from resume skills
    dimension = resume_embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(resume_embeddings)

    # Search for each job skill in resume skills
    matched = []
    missing = []

    for i, job_skill in enumerate(job_skills):
        job_vec = job_embeddings[i].reshape(1, -1)
        distances, indices = index.search(job_vec, 1)
        similarity = distances[0][0]

        if similarity >= threshold:
            matched.append(job_skill)
        else:
            missing.append(job_skill)

    total = len(job_skills)
    match_score = round((len(matched) / total) * 100, 2) if total > 0 else 0.0

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "match_score": match_score
    }

def analyze_skill_gap(resume_text: str, job_description: str) -> dict:
    resume_skills = extract_skills(resume_text)
    job_skills = extract_job_skills(job_description)
    result = compute_skill_gap(resume_skills, job_skills)
    result["resume_skills"] = resume_skills
    result["job_skills"] = job_skills
    return result