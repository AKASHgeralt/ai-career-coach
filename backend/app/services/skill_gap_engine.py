import re

from app.services.nlp import find_skills_in_text
from app.services.skill_similarity import similarity

def extract_job_skills(job_description: str) -> list[str]:
    return find_skills_in_text(job_description)

# Baseline skill expectations per role, used when a job description is too
# thin to extract real signal from (e.g. "I want to be a data scientist").
# Ordered most-specific first so e.g. "machine learning engineer" is checked
# before a generic "engineer" fallback would apply.
ROLE_SKILL_PROFILES = [
    (["data scientist"], ["python", "r", "sql", "machine learning", "deep learning", "pandas", "numpy", "scikit-learn", "tensorflow", "matplotlib", "tableau", "power bi", "spark"]),
    (["machine learning engineer", "ml engineer", "ai engineer"], ["python", "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "docker", "aws", "sql", "nlp", "computer vision"]),
    (["data engineer"], ["python", "sql", "spark", "hadoop", "airflow", "postgresql", "aws", "docker", "kubernetes"]),
    (["data analyst"], ["sql", "excel", "tableau", "power bi", "python", "pandas", "numpy"]),
    (["backend engineer", "backend developer"], ["python", "java", "nodejs", "django", "fastapi", "flask", "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes", "aws", "rest api", "microservices", "sql", "git"]),
    (["frontend engineer", "frontend developer"], ["javascript", "typescript", "react", "angular", "vue", "html", "css", "tailwind", "nextjs", "git", "rest api", "graphql"]),
    (["full stack developer", "fullstack developer", "full stack engineer", "fullstack engineer"], ["javascript", "typescript", "react", "nodejs", "express", "python", "sql", "postgresql", "mongodb", "docker", "git", "rest api", "html", "css"]),
    (["devops engineer"], ["docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ansible", "jenkins", "ci/cd", "linux", "nginx", "github actions", "git"]),
    (["site reliability engineer", "sre"], ["linux", "docker", "kubernetes", "aws", "terraform", "ci/cd", "nginx"]),
    (["cloud engineer", "cloud architect"], ["aws", "gcp", "azure", "docker", "kubernetes", "terraform", "linux", "ci/cd"]),
    (["database administrator", "dba"], ["postgresql", "mysql", "sql", "mongodb", "redis"]),
    (["android developer"], ["kotlin", "java", "git"]),
    (["ios developer"], ["swift", "git"]),
    (["qa engineer", "test engineer", "sdet"], ["postman", "jira", "git", "agile", "sql"]),
    (["product manager"], ["agile", "scrum", "jira", "sql"]),
    (["ui/ux designer", "ux designer", "product designer", "ui designer"], ["figma"]),
    (["software engineer", "software developer", "swe", "sde"], ["python", "java", "javascript", "git", "sql", "docker", "rest api", "agile", "github"]),
]

GENERIC_TECH_SKILLS = ["python", "javascript", "sql", "git", "docker", "rest api", "agile"]

def skills_for_role(job_title: str) -> list[str]:
    """Best-guess baseline skillset for a job title, used as a fallback."""
    if not job_title:
        return []
    title_lower = job_title.lower()
    for aliases, skills in ROLE_SKILL_PROFILES:
        if any(re.search(rf"\b{re.escape(alias)}\b", title_lower) for alias in aliases):
            return skills
    if re.search(r"\b(engineer|developer|programmer|coder)\b", title_lower):
        return GENERIC_TECH_SKILLS
    return []

# A skill scoring at or above MATCH_THRESHOLD counts as held. Between
# PARTIAL_THRESHOLD and MATCH_THRESHOLD it's adjacent knowledge — worth showing
# separately, because "you're close" is different advice from "start here".
MATCH_THRESHOLD = 0.75
PARTIAL_THRESHOLD = 0.50

STATUS_MATCHED = "MATCHED"
STATUS_PARTIAL = "PARTIAL"
STATUS_MISSING = "MISSING"


def classify_similarity(score: float) -> str:
    # Parameter is `score`, not `similarity`, to avoid shadowing the imported
    # similarity() lookup used elsewhere in this module.
    if score >= MATCH_THRESHOLD:
        return STATUS_MATCHED
    if score >= PARTIAL_THRESHOLD:
        return STATUS_PARTIAL
    return STATUS_MISSING


def compute_skill_gap(resume_skills: list[str], job_skills: list[str], threshold: float = MATCH_THRESHOLD) -> dict:
    if not resume_skills or not job_skills:
        return {
            "matched_skills": [],
            "partial_skills": [],
            "missing_skills": job_skills,
            "match_score": 0.0,
            "skill_details": [
                {"skill": s, "status": STATUS_MISSING, "similarity": 0.0}
                for s in job_skills
            ],
        }

    # Exact matches first — these are unambiguous, no embedding guesswork needed.
    resume_set = set(resume_skills)
    matched = [skill for skill in job_skills if skill in resume_set]
    unresolved = [skill for skill in job_skills if skill not in resume_set]

    # Similarity per job skill, so the UI can show *why* something is missing
    # rather than just that it is. Exact hits are 1.0 by definition.
    similarities = {skill: 1.0 for skill in matched}

    # Anything not an exact match is scored against a precomputed similarity
    # table. This produces identical results to the embedding model it was
    # generated from: SKILLS_DB is a closed vocabulary, so every related pair
    # the model recognised is already enumerated in that table. See
    # skill_similarity.py for why carrying torch to recompute it was a bad
    # trade.
    for job_skill in unresolved:
        best = max((similarity(job_skill, rs) for rs in resume_skills), default=0.0)
        similarities[job_skill] = best
        if best >= threshold:
            matched.append(job_skill)

    matched_set = set(matched)
    # Unchanged contract: anything not matched is still reported as missing,
    # so existing callers and stored rows keep the same meaning.
    missing = [skill for skill in job_skills if skill not in matched_set]

    skill_details = [
        {
            "skill": skill,
            "status": classify_similarity(similarities.get(skill, 0.0)),
            "similarity": round(similarities.get(skill, 0.0), 3),
        }
        for skill in job_skills
    ]
    # Partial is a presentational subdivision of "missing" — deliberately not
    # counted as a match, so match_score is identical to before.
    partial = [d["skill"] for d in skill_details if d["status"] == STATUS_PARTIAL]

    total = len(job_skills)
    match_score = round((len(matched) / total) * 100, 2) if total > 0 else 0.0

    return {
        "matched_skills": matched,
        "partial_skills": partial,
        "missing_skills": missing,
        "match_score": match_score,
        "skill_details": skill_details,
    }

def analyze_skill_gap(resume_text: str, job_description: str, job_title: str = "") -> dict:
    resume_skills = find_skills_in_text(resume_text)
    job_skills = extract_job_skills(job_description)

    # A thin/vague description (e.g. "I want to be a data scientist") carries
    # almost no extractable signal on its own — fall back to what the role
    # typically requires rather than reporting a hollow 0% match.
    used_role_fallback = False
    if len(job_skills) < 2:
        role_skills = skills_for_role(job_title)
        if role_skills:
            job_skills = sorted(set(job_skills) | set(role_skills))
            used_role_fallback = True

    result = compute_skill_gap(resume_skills, job_skills)
    result["resume_skills"] = resume_skills
    result["job_skills"] = job_skills
    result["used_role_fallback"] = used_role_fallback
    return result