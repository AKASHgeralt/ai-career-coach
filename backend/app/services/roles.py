"""Canonical catalogue of target career roles.

This is the single place a new supported role gets added. Each entry carries a
stable `slug` (what we persist and what the API accepts), a human `label`, and
a `match_title` which is fed to skill_gap_engine.skills_for_role() so the role
resolves to an existing baseline skill profile.

Adding a role = appending one entry here. If the role has no matching profile
in ROLE_SKILL_PROFILES, add that profile too and the rest of the system picks
it up with no further changes.
"""

TARGET_ROLES = [
    {"slug": "data-scientist", "label": "Data Scientist", "match_title": "data scientist"},
    {"slug": "machine-learning-engineer", "label": "Machine Learning Engineer", "match_title": "machine learning engineer"},
    {"slug": "ai-engineer", "label": "AI Engineer", "match_title": "ai engineer"},
    {"slug": "backend-developer", "label": "Backend Developer", "match_title": "backend developer"},
    {"slug": "full-stack-developer", "label": "Full Stack Developer", "match_title": "full stack developer"},
    {"slug": "data-analyst", "label": "Data Analyst", "match_title": "data analyst"},
    {"slug": "software-engineer", "label": "Software Engineer", "match_title": "software engineer"},
]

ROLES_BY_SLUG = {role["slug"]: role for role in TARGET_ROLES}

VALID_ROLE_SLUGS = tuple(role["slug"] for role in TARGET_ROLES)


def is_valid_role(slug: str | None) -> bool:
    return slug in ROLES_BY_SLUG


def role_label(slug: str | None) -> str | None:
    """Human-readable name, e.g. 'ai-engineer' -> 'AI Engineer'."""
    role = ROLES_BY_SLUG.get(slug or "")
    return role["label"] if role else None


def role_match_title(slug: str | None) -> str:
    """Title string understood by skill_gap_engine.skills_for_role().

    Returns "" for an unknown/unset role so callers can pass it through
    without branching — skills_for_role("") simply yields no baseline.
    """
    role = ROLES_BY_SLUG.get(slug or "")
    return role["match_title"] if role else ""
