"""Test fixtures providing an isolated database.

Integration tests run against a throwaway PostgreSQL *schema* in the same
database, built by running the real Alembic migrations. That means:

  * no test ever touches development data
  * the schema under test is exactly what migrations produce, so a broken
    migration fails the suite rather than surfacing in production
  * a schema is used rather than a separate database because the application
    role doesn't have CREATE DATABASE

The schema is dropped afterwards regardless of outcome.
"""
import os
import subprocess
import sys
from urllib.parse import urlsplit, urlunsplit

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND, ".env"))

TEST_SCHEMA = "career_coach_test"

def _schema_url(base_url: str, schema: str) -> str:
    parts = urlsplit(base_url)
    return urlunsplit((
        parts.scheme, parts.netloc, parts.path,
        f"options=-csearch_path%3D{schema}", "",
    ))


@pytest.fixture(scope="session")
def database_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL is not set; integration tests need a database")
    return url


@pytest.fixture(scope="session")
def test_schema(database_url):
    """Create the schema, migrate it, drop it at the end of the session."""
    admin = sa.create_engine(database_url, isolation_level="AUTOCOMMIT")

    def drop():
        with admin.connect() as c:
            c.execute(sa.text(f'DROP SCHEMA IF EXISTS "{TEST_SCHEMA}" CASCADE'))

    drop()
    with admin.connect() as c:
        c.execute(sa.text(f'CREATE SCHEMA "{TEST_SCHEMA}"'))

    result = subprocess.run(
        [os.path.join(BACKEND, "venv", "Scripts", "alembic.exe"), "upgrade", "head"],
        env=dict(os.environ, ALEMBIC_DATABASE_URL=_schema_url(database_url, TEST_SCHEMA)),
        cwd=BACKEND, capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        drop()
        pytest.fail(f"migrations failed against the test schema:\n{result.stderr[-1500:]}")

    yield _schema_url(database_url, TEST_SCHEMA)
    drop()


@pytest.fixture(scope="session")
def app(test_schema):
    """The FastAPI app with its database dependency pointed at the test schema."""
    import main
    from database import get_db

    engine = sa.create_engine(test_schema, poolclass=sa.pool.NullPool)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[get_db] = override_get_db
    yield main.app
    main.app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_tables(request):
    """Empty every table between tests so cases can't leak into each other.

    `test_schema` is resolved lazily via getfixturevalue rather than declared as
    a parameter: declaring it would make this autouse fixture drag a database
    into every pure unit test in the suite.
    """
    if "client" not in request.fixturenames:
        yield
        return

    # Auth endpoints are rate limited per client address. Every test hits them
    # from the same address, so without a reset the suite throttles itself
    # after a handful of cases.
    from app.services.rate_limit import login_limiter, register_limiter
    login_limiter.reset()
    register_limiter.reset()

    test_schema = request.getfixturevalue("test_schema")
    engine = sa.create_engine(test_schema, isolation_level="AUTOCOMMIT", poolclass=sa.pool.NullPool)
    with engine.connect() as c:
        c.execute(sa.text(
            "TRUNCATE roadmap_tasks, recommendations, skill_gaps, interview_answers, "
            "interview_sessions, github_profiles, resumes, users CASCADE"
        ))
    engine.dispose()
    yield


def register_and_login(client, email="a@example.com", password="password123", name="Test User"):
    """Create a user and return an Authorization header for them."""
    client.post("/api/auth/register", json={
        "full_name": name, "email": email, "password": password,
    })
    token = client.post("/api/auth/login", data={
        "username": email, "password": password,
    }).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth(client):
    return register_and_login(client)


@pytest.fixture
def other_auth(client):
    """A second, unrelated user — used to prove data isolation."""
    return register_and_login(client, email="b@example.com", name="Other User")


def make_pdf(text: str = "Python SQL Docker AWS REST API experience education skills") -> bytes:
    """A genuine PDF containing `text`.

    Built with PyMuPDF rather than hand-written bytes so the document actually
    has an extractable text layer — endpoints that need parsed text reject an
    empty one, which is correct behaviour and shouldn't be worked around.
    """
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data
