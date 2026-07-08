"""Database engine and session management."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _make_engine():
    url = settings.sqlalchemy_url
    if not url:
        # Deferred: the app can import without a DB configured; endpoints that
        # need the DB will raise a clear error when first used.
        return None
    return create_engine(url, pool_pre_ping=True, future=True)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False) if engine else None


def get_session() -> Iterator[Session]:
    if SessionLocal is None:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy api/.env.example to api/.env and add your "
            "Supabase connection string."
        )
    with SessionLocal() as session:
        yield session
