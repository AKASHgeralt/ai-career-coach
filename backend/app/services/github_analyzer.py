import httpx
from collections import Counter

def fetch_github_data(username: str) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}

    with httpx.Client() as client:
        # Fetch user profile
        user_resp = client.get(
            f"https://api.github.com/users/{username}",
            headers=headers
        )
        if user_resp.status_code == 404:
            raise ValueError(f"GitHub user '{username}' not found")
        if user_resp.status_code != 200:
            raise ValueError("GitHub API error")

        user_data = user_resp.json()

        # Fetch repositories
        repos_resp = client.get(
            f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",
            headers=headers
        )
        repos_data = repos_resp.json() if repos_resp.status_code == 200 else []

    # Analyze repos
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
                "updated_at": repo.get("updated_at", "")
            })

    # Top languages
    lang_counter = Counter(languages)
    top_languages = [{"language": lang, "count": count}
                     for lang, count in lang_counter.most_common(5)]

    # Calculate developer score
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
        "repos": repo_list[:10],
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