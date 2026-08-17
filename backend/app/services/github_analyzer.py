import os
from collections import Counter
from datetime import datetime, timezone

import httpx

GITHUB_API = "https://api.github.com"

# Unauthenticated GitHub allows 60 requests/hour per IP, and each sync costs
# two. Setting GITHUB_TOKEN raises that to 5000/hour.
REQUEST_TIMEOUT = 15.0


class GitHubError(RuntimeError):
    """Base for GitHub API problems that should reach the user intelligibly."""


class GitHubNotFound(GitHubError):
    pass


class GitHubRateLimited(GitHubError):
    """Rate limit exhausted. Carries when it resets so the UI can say so."""

    def __init__(self, message: str, reset_at: datetime | None = None, authenticated: bool = False):
        super().__init__(message)
        self.reset_at = reset_at
        self.authenticated = authenticated


class GitHubUnavailable(GitHubError):
    pass


def _headers() -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _reset_time(response: httpx.Response) -> datetime | None:
    raw = response.headers.get("X-RateLimit-Reset")
    if not raw:
        return None
    try:
        return datetime.fromtimestamp(int(raw), tz=timezone.utc)
    except (TypeError, ValueError):
        return None


def _raise_for_rate_limit(response: httpx.Response) -> None:
    """Turn GitHub's rate-limit responses into an actionable error.

    GitHub signals exhaustion with 403 (or 429) plus X-RateLimit-Remaining: 0,
    which is easy to mistake for a permissions problem.
    """
    remaining = response.headers.get("X-RateLimit-Remaining")
    if response.status_code in (403, 429) and remaining == "0":
        reset_at = _reset_time(response)
        authenticated = bool(os.getenv("GITHUB_TOKEN"))
        when = ""
        if reset_at:
            minutes = max(1, round((reset_at - datetime.now(timezone.utc)).total_seconds() / 60))
            when = f" Try again in about {minutes} minute{'s' if minutes != 1 else ''}."
        hint = "" if authenticated else " Setting a GITHUB_TOKEN raises the limit from 60 to 5000 requests per hour."
        raise GitHubRateLimited(
            f"GitHub's API rate limit has been reached.{when}{hint}".strip(),
            reset_at=reset_at,
            authenticated=authenticated,
        )


def fetch_github_data(username: str) -> dict:
    headers = _headers()

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            user_resp = client.get(f"{GITHUB_API}/users/{username}", headers=headers)

            _raise_for_rate_limit(user_resp)
            if user_resp.status_code == 404:
                raise GitHubNotFound(f"GitHub user '{username}' not found")
            if user_resp.status_code != 200:
                raise GitHubUnavailable(
                    f"GitHub returned an unexpected response ({user_resp.status_code})"
                )

            user_data = user_resp.json()

            repos_resp = client.get(
                f"{GITHUB_API}/users/{username}/repos?per_page=100&sort=updated",
                headers=headers,
            )
            _raise_for_rate_limit(repos_resp)
            repos_data = repos_resp.json() if repos_resp.status_code == 200 else []
    except GitHubError:
        raise
    except httpx.TimeoutException:
        raise GitHubUnavailable("GitHub took too long to respond. Please try again.")
    except httpx.HTTPError:
        raise GitHubUnavailable("Could not reach GitHub. Please check your connection.")

    languages = []
    total_stars = 0
    repo_list = []

    for repo in repos_data:
        if not repo.get("fork"):
            if repo.get("language"):
                languages.append(repo["language"])
            total_stars += repo.get("stargazers_count", 0)
            repo_list.append({
                "name": repo["name"],
                "description": repo.get("description", ""),
                "language": repo.get("language", ""),
                "stars": repo.get("stargazers_count", 0),
                "url": repo.get("html_url", ""),
                "updated_at": repo.get("updated_at", ""),
            })

    lang_counter = Counter(languages)
    top_languages = [{"language": lang, "count": count}
                     for lang, count in lang_counter.most_common(5)]

    score = calculate_developer_score(
        repo_count=len(repo_list),
        total_stars=total_stars,
        languages=list(lang_counter.keys()),
        followers=user_data.get("followers", 0)
    )

    return {
        "github_username": username,
        "repo_count": len(repo_list),
        "total_stars": total_stars,
        "top_languages": top_languages,
        # Full list retained for insight analysis; the API response trims it.
        "repos": repo_list,
        "developer_score": score,
        "followers": user_data.get("followers", 0),
        "following": user_data.get("following", 0),
        "name": user_data.get("name", ""),
        "bio": user_data.get("bio", ""),
        "avatar_url": user_data.get("avatar_url", ""),
    }


def calculate_developer_score(
    repo_count: int,
    total_stars: int,
    languages: list,
    followers: int
) -> float:
    score = 0.0

    # Repos (max 30 points)
    score += min(repo_count * 2, 30)

    # Stars (max 25 points)
    score += min(total_stars * 2, 25)

    # Language diversity (max 20 points)
    score += min(len(languages) * 4, 20)

    # Followers (max 15 points)
    score += min(followers * 0.5, 15)

    # Bonus for being active (max 10 points)
    if repo_count >= 5: score += 5
    if repo_count >= 10: score += 5

    return round(min(score, 100), 1)
