"""Integration tests for registration, login and route protection.

These exercise the real routers against a migrated throwaway schema.
"""
import pytest

pytestmark = pytest.mark.integration


class TestRegistration:
    def test_creates_a_user(self, client):
        r = client.post("/api/auth/register", json={
            "full_name": "Ada Lovelace", "email": "ada@example.com", "password": "secret123",
        })
        assert r.status_code == 201
        body = r.json()
        assert body["email"] == "ada@example.com"
        assert body["target_role"] is None

    def test_never_returns_the_password(self, client):
        r = client.post("/api/auth/register", json={
            "full_name": "Ada", "email": "ada@example.com", "password": "secret123",
        })
        assert "password" not in r.text.lower() or "secret123" not in r.text

    def test_duplicate_email_is_rejected(self, client):
        payload = {"full_name": "Ada", "email": "dup@example.com", "password": "secret123"}
        assert client.post("/api/auth/register", json=payload).status_code == 201
        r = client.post("/api/auth/register", json=payload)
        assert r.status_code == 400
        assert "already registered" in r.json()["detail"].lower()

    def test_malformed_email_is_rejected(self, client):
        r = client.post("/api/auth/register", json={
            "full_name": "Ada", "email": "not-an-email", "password": "secret123",
        })
        assert r.status_code == 422

    def test_missing_fields_are_rejected(self, client):
        assert client.post("/api/auth/register", json={"email": "a@b.com"}).status_code == 422


class TestLogin:
    def test_valid_credentials_return_a_token(self, client):
        client.post("/api/auth/register", json={
            "full_name": "Ada", "email": "ada@example.com", "password": "secret123",
        })
        r = client.post("/api/auth/login", data={
            "username": "ada@example.com", "password": "secret123",
        })
        assert r.status_code == 200
        assert r.json()["token_type"] == "bearer"
        assert r.json()["access_token"]

    def test_wrong_password_is_401(self, client):
        client.post("/api/auth/register", json={
            "full_name": "Ada", "email": "ada@example.com", "password": "secret123",
        })
        r = client.post("/api/auth/login", data={
            "username": "ada@example.com", "password": "wrong",
        })
        assert r.status_code == 401

    def test_unknown_user_is_401(self, client):
        r = client.post("/api/auth/login", data={
            "username": "nobody@example.com", "password": "secret123",
        })
        assert r.status_code == 401

    def test_unknown_user_and_wrong_password_are_indistinguishable(self, client):
        """Identical responses avoid revealing which emails are registered."""
        client.post("/api/auth/register", json={
            "full_name": "Ada", "email": "ada@example.com", "password": "secret123",
        })
        wrong_pw = client.post("/api/auth/login", data={"username": "ada@example.com", "password": "nope"})
        no_user = client.post("/api/auth/login", data={"username": "ghost@example.com", "password": "nope"})
        assert wrong_pw.status_code == no_user.status_code
        assert wrong_pw.json()["detail"] == no_user.json()["detail"]


PROTECTED = [
    ("get", "/api/users/me"),
    ("get", "/api/resumes"),
    ("get", "/api/resumes/versions"),
    ("get", "/api/skills/gaps/11111111-1111-1111-1111-111111111111"),
    ("get", "/api/interview/sessions"),
    ("get", "/api/github/profile"),
    ("get", "/api/analytics/summary"),
    ("get", "/api/analytics/readiness"),
    ("get", "/api/analytics/timeline"),
]


class TestRouteProtection:
    @pytest.mark.parametrize("method,path", PROTECTED)
    def test_requires_a_token(self, client, method, path):
        assert getattr(client, method)(path).status_code == 401

    @pytest.mark.parametrize("method,path", PROTECTED)
    def test_rejects_a_garbage_token(self, client, method, path):
        r = getattr(client, method)(path, headers={"Authorization": "Bearer not-a-jwt"})
        assert r.status_code == 401

    def test_rejects_a_token_signed_with_the_wrong_key(self, client):
        from jose import jwt
        forged = jwt.encode({"sub": "11111111-1111-1111-1111-111111111111"}, "wrong-key", algorithm="HS256")
        r = client.get("/api/users/me", headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code == 401

    def test_rejects_an_expired_token(self, client, auth):
        from datetime import datetime, timedelta
        from app.services.auth import SECRET_KEY, ALGORITHM
        from jose import jwt
        expired = jwt.encode(
            {"sub": "11111111-1111-1111-1111-111111111111",
             "exp": datetime.utcnow() - timedelta(minutes=1)},
            SECRET_KEY, algorithm=ALGORITHM,
        )
        r = client.get("/api/users/me", headers={"Authorization": f"Bearer {expired}"})
        assert r.status_code == 401

    def test_valid_token_is_accepted(self, client, auth):
        assert client.get("/api/users/me", headers=auth).status_code == 200


class TestTargetRole:
    def test_set_and_read_back(self, client, auth):
        r = client.put("/api/users/me/target-role", json={"target_role": "ai-engineer"}, headers=auth)
        assert r.status_code == 200
        assert r.json()["target_role_label"] == "AI Engineer"
        assert client.get("/api/users/me", headers=auth).json()["target_role"] == "ai-engineer"

    def test_unknown_role_is_rejected(self, client, auth):
        r = client.put("/api/users/me/target-role", json={"target_role": "wizard"}, headers=auth)
        assert r.status_code == 422

    def test_catalogue_lists_every_role(self, client):
        r = client.get("/api/users/target-roles")
        assert r.status_code == 200
        slugs = [x["slug"] for x in r.json()]
        assert "ai-engineer" in slugs and len(slugs) == 7
