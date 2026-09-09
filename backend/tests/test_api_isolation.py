"""Integration tests for per-user data isolation.

The property under test: authenticating as one user must never grant read or
write access to another user's data. Every router filters by user_id, and these
tests assert that filter actually holds at the HTTP boundary — a missing clause
would be a serious data leak rather than a cosmetic bug.

A 404 (rather than 403) is the expected response: it doesn't confirm that
someone else's resource exists.
"""
import io

import pytest

pytestmark = pytest.mark.integration

from tests.conftest import make_pdf


def upload(client, headers, name="cv.pdf", text=None):
    """Upload a real PDF with an extractable text layer.

    Endpoints that need parsed text legitimately reject an empty document, so
    the fixture produces a genuine one rather than working around that.
    """
    payload = make_pdf(text) if text else make_pdf()
    r = client.post("/api/resumes/upload", headers=headers,
                    files={"file": (name, io.BytesIO(payload), "application/pdf")})
    assert r.status_code == 201, r.text
    return r.json()


class TestResumeIsolation:
    def test_listing_only_returns_your_own(self, client, auth, other_auth):
        upload(client, auth, "mine.pdf")
        upload(client, other_auth, "theirs.pdf")

        mine = client.get("/api/resumes", headers=auth).json()
        assert [r["file_name"] for r in mine] == ["mine.pdf"]

    def test_cannot_read_another_users_resume(self, client, auth, other_auth):
        theirs = upload(client, other_auth)
        r = client.get(f"/api/resumes/{theirs['id']}", headers=auth)
        assert r.status_code == 404

    def test_cannot_analyse_another_users_resume(self, client, auth, other_auth):
        theirs = upload(client, other_auth)
        r = client.get(f"/api/resumes/{theirs['id']}/analyze", headers=auth)
        assert r.status_code == 404

    def test_cannot_delete_another_users_resume(self, client, auth, other_auth):
        theirs = upload(client, other_auth)
        assert client.delete(f"/api/resumes/{theirs['id']}", headers=auth).status_code == 404
        # still there for its owner
        assert client.get(f"/api/resumes/{theirs['id']}", headers=other_auth).status_code == 200

    def test_cannot_compare_against_another_users_resume(self, client, auth, other_auth):
        mine = upload(client, auth, "mine.pdf")
        theirs = upload(client, other_auth, "theirs.pdf")
        r = client.get(f"/api/resumes/compare?base={mine['id']}&target={theirs['id']}", headers=auth)
        assert r.status_code == 404

    def test_versions_are_numbered_per_user(self, client, auth, other_auth):
        """Two users uploading must each start at v1."""
        assert upload(client, auth, "a.pdf")["version"] == 1
        assert upload(client, other_auth, "b.pdf")["version"] == 1
        assert upload(client, auth, "a2.pdf")["version"] == 2


class TestSkillGapIsolation:
    def _make_gap(self, client, headers):
        resume = upload(client, headers)
        r = client.post("/api/skills/analyze", headers=headers, json={
            "resume_id": resume["id"], "job_title": "Backend Developer",
            "job_description": "python sql docker aws rest api",
        })
        assert r.status_code == 201, r.text
        return resume, r.json()

    def test_cannot_list_another_users_gaps(self, client, auth, other_auth):
        their_resume, _ = self._make_gap(client, other_auth)
        r = client.get(f"/api/skills/gaps/{their_resume['id']}", headers=auth)
        assert r.status_code == 200
        assert r.json() == []          # filtered out, not leaked

    def test_cannot_analyse_using_another_users_resume(self, client, auth, other_auth):
        theirs = upload(client, other_auth)
        r = client.post("/api/skills/analyze", headers=auth, json={
            "resume_id": theirs["id"], "job_title": "X", "job_description": "python",
        })
        assert r.status_code == 404

    def test_cannot_read_another_users_recommendations(self, client, auth, other_auth):
        _, their_gap = self._make_gap(client, other_auth)
        assert client.get(f"/api/recommendations/{their_gap['id']}", headers=auth).status_code == 404
        assert client.get(f"/api/recommendations/{their_gap['id']}/tasks", headers=auth).status_code == 404


class TestInterviewIsolation:
    def _session(self, client, headers, monkeypatch=None):
        return client.post("/api/interview/start", headers=headers,
                           json={"job_role": "Backend Developer", "difficulty": "easy"})

    def test_cannot_list_another_users_sessions(self, client, auth, other_auth, monkeypatch):
        from app.routers import interview as interview_router
        monkeypatch.setattr(interview_router, "generate_question", lambda *a, **k: "Q?")
        self._session(client, other_auth)
        assert client.get("/api/interview/sessions", headers=auth).json() == []

    def test_cannot_read_another_users_answers(self, client, auth, other_auth, monkeypatch):
        from app.routers import interview as interview_router
        monkeypatch.setattr(interview_router, "generate_question", lambda *a, **k: "Q?")
        theirs = self._session(client, other_auth).json()
        sid = theirs["session_id"]
        assert client.get(f"/api/interview/sessions/{sid}/answers", headers=auth).status_code == 404
        assert client.get(f"/api/interview/sessions/{sid}/analytics", headers=auth).status_code == 404

    def test_cannot_answer_another_users_session(self, client, auth, other_auth, monkeypatch):
        from app.routers import interview as interview_router
        monkeypatch.setattr(interview_router, "generate_question", lambda *a, **k: "Q?")
        theirs = self._session(client, other_auth).json()
        r = client.post("/api/interview/answer", headers=auth,
                        json={"session_id": theirs["session_id"], "answer": "hello"})
        assert r.status_code == 404


class TestGitHubIsolation:
    def test_profile_is_per_user(self, client, auth, other_auth, monkeypatch):
        from app.services import github_analyzer
        from app.routers import github as github_router

        monkeypatch.setattr(github_router, "fetch_github_data", lambda u: {
            "github_username": u, "repo_count": 3, "total_stars": 5,
            "top_languages": [{"language": "Python", "count": 3}], "repos": [],
            "developer_score": 42.0, "followers": 1, "following": 1,
        })
        client.post("/api/github/connect", headers=other_auth, json={"github_username": "them"})

        # the other user's profile must not be visible
        assert client.get("/api/github/profile", headers=auth).status_code == 404
        assert client.get("/api/github/profile", headers=other_auth).json()["github_username"] == "them"


class TestAnalyticsIsolation:
    def test_summary_counts_only_your_own_data(self, client, auth, other_auth):
        upload(client, other_auth, "theirs.pdf")
        upload(client, other_auth, "theirs2.pdf")
        summary = client.get("/api/analytics/summary", headers=auth).json()
        assert summary["resumes"]["count"] == 0

    def test_readiness_ignores_other_users(self, client, auth, other_auth):
        upload(client, other_auth)
        readiness = client.get("/api/analytics/readiness", headers=auth).json()
        assert readiness["score"] is None
        assert set(readiness["missing"]) == {"resume", "skills", "interview", "github"}

    def test_timeline_contains_only_your_events(self, client, auth, other_auth):
        upload(client, other_auth, "theirs.pdf")
        mine = upload(client, auth, "mine.pdf")
        events = client.get("/api/analytics/timeline", headers=auth).json()["events"]
        assert len(events) == 1
        assert events[0]["detail"] == "mine.pdf"


class TestNonexistentResources:
    MISSING = "11111111-1111-1111-1111-111111111111"

    def test_unknown_ids_are_404_not_500(self, client, auth):
        for path in [
            f"/api/resumes/{MISSING}" if False else f"/api/resumes/{'11111111-1111-1111-1111-111111111111'}",
            "/api/recommendations/11111111-1111-1111-1111-111111111111",
            "/api/interview/sessions/11111111-1111-1111-1111-111111111111/answers",
        ]:
            assert client.get(path, headers=auth).status_code == 404, path

    def test_malformed_uuid_is_422_not_500(self, client, auth):
        """A non-UUID must be rejected at validation, never reach the database."""
        for path in [
            "/api/resumes/not-a-uuid",
            "/api/recommendations/not-a-uuid",
            "/api/skills/gaps/not-a-uuid",
            "/api/interview/sessions/not-a-uuid/answers",
        ]:
            assert client.get(path, headers=auth).status_code == 422, path
