import re

# spaCy was loaded here but its pipeline was never invoked — all extraction
# below is regex and keyword based. Loading en_core_web_sm cost several seconds
# of startup for nothing, so the import was removed.

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

# Common shorthand/spelling variants mapped to their canonical SKILLS_DB entry,
# so e.g. "JS" and "Postgres" are recognized as the same skill as "javascript"/"postgresql".
SKILL_ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "golang": "go",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "ml": "machine learning",
    "cv": "computer vision",
    "py": "python",
    "node": "nodejs",
    "node.js": "nodejs",
    "next.js": "nextjs",
    "vue.js": "vue",
    "sklearn": "scikit-learn",
    "cicd": "ci/cd",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
}

# Skills containing regex-special characters (c++, c#, ci/cd) can't safely use
# \b word-boundary matching, so they fall back to plain substring search —
# they're distinctive enough that false positives are effectively a non-issue.
_PLAIN_TEXT_SKILLS = {s for s in SKILLS_DB if re.fullmatch(r"[a-z0-9 .]+", s)}

def _skill_pattern(skill: str) -> re.Pattern:
    return re.compile(rf"\b{re.escape(skill)}\b")

_SKILL_REGEXES = {s: _skill_pattern(s) for s in SKILLS_DB if s in _PLAIN_TEXT_SKILLS}
_ALIAS_REGEXES = {
    alias: _skill_pattern(alias) if re.fullmatch(r"[a-z0-9 .]+", alias) else None
    for alias in SKILL_ALIASES
}

def find_skills_in_text(text: str) -> list[str]:
    """Detect known skills as whole words/phrases (not substrings) in free text."""
    text_lower = text.lower()
    found = set()

    for skill in SKILLS_DB:
        if skill in _SKILL_REGEXES:
            if _SKILL_REGEXES[skill].search(text_lower):
                found.add(skill)
        elif skill in text_lower:
            found.add(skill)

    for alias, canonical in SKILL_ALIASES.items():
        pattern = _ALIAS_REGEXES[alias]
        matched = pattern.search(text_lower) if pattern else alias in text_lower
        if matched:
            found.add(canonical)

    return sorted(found)

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
    return find_skills_in_text(text)

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

ATS_SECTIONS = ["experience", "education", "skills", "projects", "summary"]

# Points available per category. These sum to 100.
ATS_MAX = {
    "skills": 40,
    "length": 20,
    "education": 10,
    "experience": 10,
    "contact": 10,
    "sections": 10,
}


def calculate_ats_breakdown(text: str, skills: list[str]) -> dict:
    """Deterministic ATS score, itemised by category.

    Same arithmetic as before — this only exposes the per-category split and
    a concrete suggestion for each category that isn't maxed out, so the
    number shown to the user is fully explainable. No LLM involved.
    """
    word_count = len(text.split())
    text_lower = text.lower()

    # Skills — 4 points each, capped.
    skills_pts = min(len(skills) * 4, ATS_MAX["skills"])

    # Length — banded bonuses.
    length_pts = 0
    if word_count > 100: length_pts += 5
    if word_count > 300: length_pts += 10
    if word_count > 500: length_pts += 5

    education = extract_education(text)
    experience = extract_experience(text)
    education_pts = ATS_MAX["education"] if education else 0
    experience_pts = ATS_MAX["experience"] if experience else 0

    email, phone = extract_email(text), extract_phone(text)
    contact_pts = (5 if email else 0) + (5 if phone else 0)

    found_sections = [s for s in ATS_SECTIONS if s in text_lower]
    missing_sections = [s for s in ATS_SECTIONS if s not in text_lower]
    sections_pts = len(found_sections) * 2

    earned = {
        "skills": skills_pts,
        "length": length_pts,
        "education": education_pts,
        "experience": experience_pts,
        "contact": contact_pts,
        "sections": sections_pts,
    }

    # Suggestions are derived from the actual deficit, never invented.
    suggestions = {}
    if skills_pts < ATS_MAX["skills"]:
        needed = (ATS_MAX["skills"] - skills_pts + 3) // 4
        suggestions["skills"] = (
            f"Only {len(skills)} recognised skills found. Adding {needed} more "
            f"technologies named in your target job description would max this out."
        )
    if length_pts < ATS_MAX["length"]:
        target = 501 if word_count > 300 else (301 if word_count > 100 else 101)
        suggestions["length"] = (
            f"Your resume is {word_count} words. Reaching {target}+ words with "
            f"more detail on your projects and impact earns further points."
        )
    if not education:
        suggestions["education"] = (
            "No education detected. Add a line naming your degree and institution "
            "(e.g. 'B.Tech Computer Science, XYZ University')."
        )
    if not experience:
        suggestions["experience"] = (
            "No experience entries detected. Describe roles explicitly, e.g. "
            "'Backend Developer at Acme' or 'Software Engineering intern at Acme'."
        )
    if contact_pts < ATS_MAX["contact"]:
        missing_contact = []
        if not email: missing_contact.append("an email address")
        if not phone: missing_contact.append("a phone number")
        suggestions["contact"] = f"Add {' and '.join(missing_contact)} to your header."
    if missing_sections:
        suggestions["sections"] = (
            f"Missing standard section heading{'s' if len(missing_sections) > 1 else ''}: "
            f"{', '.join(missing_sections)}. ATS parsers look for these by name."
        )

    labels = {
        "skills": "Skills", "length": "Length", "education": "Education",
        "experience": "Experience", "contact": "Contact", "sections": "Sections",
    }

    total = min(sum(earned.values()), 100)
    return {
        "total": total,
        "components": [
            {
                "key": key,
                "label": labels[key],
                "earned": earned[key],
                "max": ATS_MAX[key],
                "suggestion": suggestions.get(key),
            }
            for key in ("skills", "length", "education", "experience", "contact", "sections")
        ],
        "word_count": word_count,
        "found_sections": found_sections,
        "missing_sections": missing_sections,
    }


def calculate_smart_ats_score(text: str, skills: list[str]) -> int:
    """Total ATS score. Kept for callers that only need the number."""
    return calculate_ats_breakdown(text, skills)["total"]

def analyze_resume(text: str) -> dict:
    skills = extract_skills(text)
    education = extract_education(text)
    experience = extract_experience(text)
    years = extract_years_of_experience(text)
    email = extract_email(text)
    phone = extract_phone(text)
    breakdown = calculate_ats_breakdown(text, skills)
    ats_score = breakdown["total"]

    return {
        "ats_breakdown": breakdown,
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