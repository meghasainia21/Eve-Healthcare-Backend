"""
Database engine + session management.

`get_db` is a FastAPI dependency that yields a single request-scoped
session and guarantees it's closed afterwards. Using SQLAlchemy's
sessionmaker directly (rather than a global session) keeps things
thread-safe under uvicorn's worker model.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# `pool_pre_ping` avoids "server closed the connection" errors after the DB
# has been idle for a while (common with default Postgres/docker setups).
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    # Needed for SQLite when used across threads (mainly for tests).
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
