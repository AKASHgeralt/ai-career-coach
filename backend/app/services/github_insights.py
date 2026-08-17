"""Deterministic strengths, weaknesses and actions from GitHub repo data.

Every statement here is derived from fields the GitHub API actually returns
(repo count, stars, language, description, updated_at, followers). Nothing is
inferred about things we cannot observe — README quality, test coverage and
pinned repositories would each need extra API calls, and guessing at them would
be making claims the data doesn't support.
"""
from datetime import datetime, timezone

# A repo untouched for this long is treated as dormant rather than active work.
STALE_DAYS = 365
DOMINANT_LANGUAGE_MIN = 3
STRONG_REPO_COUNT = 10
BROAD_LANGUAGE_COUNT = 4
NOTABLE_FOLLOWERS = 10


def _parse_updated(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def analyze_profile(profile: dict, now: datetime | None = None) -> dict:
    """Return {strengths, weaknesses, actions, stats} for a fetched profile."""
    now = now or datetime.now(timezone.utc)
    repos = profile.get("repos") or []
    repo_count = profile.get("repo_count", len(repos))
    total_stars = profile.get("total_stars", 0)
    followers = profile.get("followers", 0)
    languages = profile.get("top_languages") or []

    described = [r for r in repos if (r.get("description") or "").strip()]
    undescribed = len(repos) - len(described)
    starred = [r for r in repos if (r.get("stars") or 0) > 0]

    stale = 0
    dated = 0
    for repo in repos:
        updated = _parse_updated(repo.get("updated_at"))
        if updated:
            dated += 1
            if (now - updated).days > STALE_DAYS:
                stale += 1

    strengths, weaknesses, actions = [], [], []

    # --- strengths ---------------------------------------------------------
    if languages:
        top = languages[0]
        if top.get("count", 0) >= DOMINANT_LANGUAGE_MIN:
            strengths.append(
                f"Consistent {top['language']} work across {top['count']} repositories"
            )
    if len(languages) >= BROAD_LANGUAGE_COUNT:
        strengths.append(f"Breadth across {len(languages)} languages")
    if repo_count >= STRONG_REPO_COUNT:
        strengths.append(f"{repo_count} public repositories — sustained output")
    if total_stars > 0:
        strengths.append(
            f"{total_stars} star{'s' if total_stars != 1 else ''} earned across "
            f"{len(starred)} repositor{'ies' if len(starred) != 1 else 'y'}"
        )
    if followers >= NOTABLE_FOLLOWERS:
        strengths.append(f"{followers} followers")
    if repos and len(described) == len(repos):
        strengths.append("Every repository has a description")

    # --- weaknesses (only what the data shows) -----------------------------
    if undescribed > 0:
        weaknesses.append(
            f"{undescribed} of {len(repos)} repositories have no description"
        )
        actions.append(
            "Add a one-line description to each repository — it's the first "
            "thing a reviewer reads on your profile."
        )
    if repos and not starred:
        weaknesses.append("No repository has attracted stars yet")
        actions.append(
            "Build one portfolio-quality project and share it, rather than "
            "many small ones — stars follow depth more than volume."
        )
    if stale and dated and stale == dated:
        weaknesses.append(f"All {stale} dated repositories are over a year old")
        actions.append(
            "Push recent work. Contribution recency is visible on your profile "
            "and signals whether you're currently building."
        )
    elif stale:
        weaknesses.append(f"{stale} repositories haven't been updated in over a year")
    if repo_count < 5:
        weaknesses.append(f"Only {repo_count} public repositor{'ies' if repo_count != 1 else 'y'}")
        actions.append(
            "Publish more work — repository count is 30 of the 100 points in "
            "your developer score."
        )
    if len(languages) == 1:
        weaknesses.append(f"All public work is in {languages[0]['language']}")
        actions.append(
            "Ship something in a second language or ecosystem to show range."
        )

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "actions": actions,
        "stats": {
            "repos_with_description": len(described),
            "repos_without_description": undescribed,
            "repos_with_stars": len(starred),
            "stale_repos": stale,
            "language_count": len(languages),
        },
    }
