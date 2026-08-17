"""Tests for GitHub insights and rate-limit handling.

The key property for insights: every statement must be backed by data the API
actually returned. No claims about READMEs, tests or pinned repos, which we
never fetch.
"""
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import pytest

from app.services.github_analyzer import (
    GitHubRateLimited,
    _raise_for_rate_limit,
    calculate_developer_score,
)
from app.services.github_insights import analyze_profile

NOW = datetime(2026, 8, 16, tzinfo=timezone.utc)


def repo(name, *, stars=0, lang="Python", desc="does a thing", days_old=10):
    return {
        "name": name,
        "description": desc,
        "language": lang,
        "stars": stars,
        "url": f"https://github.com/x/{name}",
        "updated_at": (NOW - timedelta(days=days_old)).isoformat().replace("+00:00", "Z"),
    }


def profile(repos, *, followers=0, languages=None):
    langs = languages if languages is not None else [{"language": "Python", "count": len(repos)}]
    return {
        "repos": repos,
        "repo_count": len(repos),
        "total_stars": sum(r["stars"] for r in repos),
        "followers": followers,
        "top_languages": langs,
    }


class TestStrengths:
    def test_dominant_language_is_recognised(self):
        out = analyze_profile(profile([repo(f"r{i}") for i in range(4)]), now=NOW)
        assert any("Consistent Python work" in s for s in out["strengths"])

    def test_stars_are_reported_accurately(self):
        out = analyze_profile(profile([repo("a", stars=3), repo("b", stars=2)]), now=NOW)
        assert any("5 stars" in s for s in out["strengths"])

    def test_language_breadth(self):
        langs = [{"language": l, "count": 1} for l in ("Python", "Go", "Rust", "TypeScript")]
        out = analyze_profile(profile([repo("a")], languages=langs), now=NOW)
        assert any("Breadth across 4 languages" in s for s in out["strengths"])

    def test_full_descriptions_is_a_strength(self):
        out = analyze_profile(profile([repo("a"), repo("b")]), now=NOW)
        assert "Every repository has a description" in out["strengths"]


class TestWeaknesses:
    def test_counts_missing_descriptions(self):
        out = analyze_profile(
            profile([repo("a", desc=""), repo("b", desc=None), repo("c")]), now=NOW
        )
        assert any("2 of 3 repositories have no description" in w for w in out["weaknesses"])
        assert out["stats"]["repos_without_description"] == 2

    def test_no_stars_is_flagged_with_an_action(self):
        out = analyze_profile(profile([repo("a"), repo("b")]), now=NOW)
        assert any("No repository has attracted stars" in w for w in out["weaknesses"])
        assert any("portfolio-quality" in a for a in out["actions"])

    def test_stale_repositories_detected(self):
        out = analyze_profile(
            profile([repo("a", days_old=500), repo("b", days_old=5)]), now=NOW
        )
        assert any("1 repositories haven't been updated" in w for w in out["weaknesses"])
        assert out["stats"]["stale_repos"] == 1

    def test_all_stale_gets_a_stronger_message(self):
        out = analyze_profile(
            profile([repo("a", days_old=500), repo("b", days_old=600)]), now=NOW
        )
        assert any("All 2 dated repositories are over a year old" in w for w in out["weaknesses"])

    def test_single_language_is_flagged(self):
        out = analyze_profile(profile([repo("a")]), now=NOW)
        assert any("All public work is in Python" in w for w in out["weaknesses"])


class TestClaimsAreSupported:
    def test_never_mentions_data_we_do_not_fetch(self):
        """READMEs, tests and pinned repos are not in the API response we make."""
        out = analyze_profile(profile([repo("a"), repo("b", stars=4)]), now=NOW)
        text = " ".join(out["strengths"] + out["weaknesses"] + out["actions"]).lower()
        for unsupported in ("readme", "test coverage", "unit test", "pinned"):
            assert unsupported not in text

    def test_empty_profile_makes_no_claims(self):
        out = analyze_profile(profile([]), now=NOW)
        assert out["strengths"] == []
        assert not any("repositories have no description" in w for w in out["weaknesses"])

    def test_malformed_dates_do_not_crash(self):
        bad = repo("a")
        bad["updated_at"] = "not a date"
        out = analyze_profile(profile([bad]), now=NOW)
        assert out["stats"]["stale_repos"] == 0


class TestRateLimitDetection:
    def _response(self, status, remaining, reset=None):
        headers = {"X-RateLimit-Remaining": remaining}
        if reset:
            headers["X-RateLimit-Reset"] = str(int(reset.timestamp()))
        return httpx.Response(status, headers=headers, request=httpx.Request("GET", "https://x"))

    def test_403_with_zero_remaining_is_rate_limit(self):
        reset = datetime.now(timezone.utc) + timedelta(minutes=30)
        with pytest.raises(GitHubRateLimited) as exc:
            _raise_for_rate_limit(self._response(403, "0", reset))
        assert "rate limit" in str(exc.value).lower()
        assert "minute" in str(exc.value)

    def test_429_is_also_treated_as_rate_limit(self):
        with pytest.raises(GitHubRateLimited):
            _raise_for_rate_limit(self._response(429, "0"))

    def test_403_with_quota_left_is_not_rate_limit(self):
        """A genuine permissions 403 must not be mislabelled."""
        _raise_for_rate_limit(self._response(403, "42"))

    def test_200_passes_through(self):
        _raise_for_rate_limit(self._response(200, "59"))

    def test_suggests_a_token_when_unauthenticated(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with pytest.raises(GitHubRateLimited) as exc:
            _raise_for_rate_limit(self._response(403, "0"))
        assert "GITHUB_TOKEN" in str(exc.value)


class TestDeveloperScoreUnchanged:
    def test_scoring_is_preserved(self):
        # repos min(10*2,30)=20 + stars min(5*2,25)=10 + langs min(2*4,20)=8
        # + followers min(4*0.5,15)=2 + activity bonus (>=5 and >=10 repos)=10
        assert calculate_developer_score(10, 5, ["Python", "Go"], 4) == pytest.approx(50.0)

    def test_capped_at_100(self):
        assert calculate_developer_score(500, 500, ["a"] * 20, 500) == 100.0
