import spacy
import re

nlp = spacy.load("en_core_web_sm")

SKILLS_DB = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "kotlin", "swift", "php", "ruby", "scala", "r", "matlab",
    # Web
    "react", "angular", "vue", "nextjs", "nodejs", "express", "django",
    "fastapi", "flask", "html", "css", "tailwind", "bootstrap",
    # Data & ML
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "matplotlib", "opencv", "huggingface",
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "sqlite", "elasticsearch",
    "cassandra", "dynamodb",
    # DevOps & Cloud
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ansible",
    "jenkins", "github actions", "ci/cd", "nginx", "linux",
    # Tools
    "git", "github", "jira", "figma", "postman", "swagger",
    "rest api", "graphql", "microservices", "agile", "scrum",
    # Data
    "sql", "excel", "tableau", "power bi", "spark", "hadoop", "airflow",
]

EDUCATION_KEYWORDS = [
    "bachelor", "master", "phd", "b.tech", "m.tech", "b.sc", "m.sc",
    "b.e", "m.e", "mba", "bca", "mca", "diploma", "degree",
    "university", "college", "institute", "school of",
]

EXPERIENCE_KEYWORDS = [
    "experience", "worked at", "working at", "engineer at", "developer at",
    "intern at", "internship at", "employed at", "position at",
]

def extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found_skills = []
    for skill in SKILLS_DB:
        if skill in text_lower:
            found_skills.append(skill)
    return list(set(found_skills))

def extract_education(text: str) -> list[str]:
    text_lower = text.lower()
    lines = text.split("\n")
    education = []
    for line in lines:
        line_lower = line.lower().strip()
        if any(keyword in line_lower for keyword in EDUCATION_KEYWORDS):
            cleaned = line.strip()
            if len(cleaned) > 5 and len(cleaned) < 200:
                education.append(cleaned)
    return education[:5]

def extract_experience(text: str) -> list[str]:
    text_lower = text.lower()
    lines = text.split("\n")
    experience = []
    for line in lines:
        line_lower = line.lower().strip()
        if any(keyword in line_lower for keyword in EXPERIENCE_KEYWORDS):
            cleaned = line.strip()
            if len(cleaned) > 5 and len(cleaned) < 200:
                experience.append(cleaned)
    return experience[:5]

def extract_years_of_experience(text: str) -> int:
    patterns = [
        r'(\d+)\+?\s*years?\s*of\s*experience',
        r'(\d+)\+?\s*years?\s*experience',
        r'experience\s*of\s*(\d+)\+?\s*years?',
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    return 0

def extract_email(text: str) -> str | None:
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def extract_phone(text: str) -> str | None:
    pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def calculate_smart_ats_score(text: str, skills: list[str]) -> int:
    score = 0
    # Skills (max 40 points)
    score += min(len(skills) * 4, 40)
    # Length bonus (max 20 points)
    word_count = len(text.split())
    if word_count > 100: score += 5
    if word_count > 300: score += 10
    if word_count > 500: score += 5
    # Education (10 points)
    edu = extract_education(text)
    if edu: score += 10
    # Experience (10 points)
    exp = extract_experience(text)
    if exp: score += 10
    # Contact info (10 points)
    if extract_email(text): score += 5
    if extract_phone(text): score += 5
    # Key sections (10 points)
    text_lower = text.lower()
    sections = ["experience", "education", "skills", "projects", "summary"]
    for section in sections:
        if section in text_lower:
            score += 2
    return min(score, 100)

def analyze_resume(text: str) -> dict:
    skills = extract_skills(text)
    education = extract_education(text)
    experience = extract_experience(text)
    years = extract_years_of_experience(text)
    email = extract_email(text)
    phone = extract_phone(text)
    ats_score = calculate_smart_ats_score(text, skills)

    return {
        "skills": skills,
        "education": education,
        "experience": experience,
        "years_of_experience": years,
        "email": email,
        "phone": phone,
        "ats_score": ats_score,
        "skill_count": len(skills),
        "word_count": len(text.split()),
    }