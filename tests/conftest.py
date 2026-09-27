"""
Shared pytest fixtures.

We test against a real PostgreSQL database (not SQLite) so that things
like our `Enum` columns, `Numeric` precision and unique constraints behave
exactly as they will in production - SQLite is lenient about a lot of
this in ways that can hide real bugs.

Point `TEST_DATABASE_URL` at a throwaway Postgres database. `docker-compose`
already provisions one; see README "Testing instructions".
"""

import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/eve_healthcare_test"
    ),
)

from app.db.base import Base  # noqa: E402  (must import after DATABASE_URL is set)
from app.db.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.core.security import hash_password  # noqa: E402

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/eve_healthcare_test"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    """Truncate every table before each test so tests are fully isolated."""
    with engine.begin() as connection:
        table_names = ", ".join(t.name for t in reversed(Base.metadata.sorted_tables))
        connection.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    # Each request gets its OWN session (exactly like production's `get_db`),
    # rather than reusing `db_session`. This matters for concurrency tests:
    # a single SQLAlchemy Session is not thread-safe, so sharing one across
    # simultaneous requests would test nothing meaningful about real races.
    def _override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session):
    """Factory fixture: create a user directly in the DB (bypassing the API)."""

    def _make_user(
        email: str = "user@example.com",
        password: str = "UserPass123",
        name: str = "Test User",
        role: UserRole = UserRole.USER,
    ) -> User:
        user = User(name=name, email=email, password_hash=hash_password(password), role=role)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make_user


@pytest.fixture
def auth_headers(client):
    """Factory fixture: sign up + log in a fresh user, return auth headers."""

    def _auth_headers(email: str = "user@example.com", password: str = "UserPass123"):
        client.post("/auth/signup", json={"name": "Test User", "email": email, "password": password})
        r = client.post("/auth/login", json={"email": email, "password": password})
        token = r.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers


@pytest.fixture
def admin_headers(client, db_session):
    """Create an admin user directly (signup can't create admins) and log in."""

    def _admin_headers(email: str = "admin@example.com", password: str = "AdminPass123"):
        user = User(
            name="Admin",
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
        )
        db_session.add(user)
        db_session.commit()
        r = client.post("/auth/login", json={"email": email, "password": password})
        token = r.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _admin_headers


@pytest.fixture
def seeded_center_and_test(db_session):
    """Create one diagnostic centre offering one test, return (center, test, offering)."""
    from app.models.center_test_offering import CenterTestOffering
    from app.models.diagnostic_center import DiagnosticCenter
    from app.models.diagnostic_test import DiagnosticTest

    center = DiagnosticCenter(name="Test Diagnostics", location="Test City")
    test = DiagnosticTest(name="Sample Test", description="A sample test")
    db_session.add_all([center, test])
    db_session.flush()

    offering = CenterTestOffering(center_id=center.id, test_id=test.id, price=250)
    db_session.add(offering)
    db_session.commit()
    db_session.refresh(center)
    db_session.refresh(test)
    db_session.refresh(offering)
    return center, test, offering


def future_iso(days: int = 2) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def past_iso(days: int = 1) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
