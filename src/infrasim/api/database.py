"""SQLAlchemy async database layer for InfraSim SaaS persistence."""

from __future__ import annotations

import datetime as _dt
from pathlib import Path

from sqlalchemy import DateTime, Float, String, Text, ForeignKey, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# ---------------------------------------------------------------------------
# Database path
# ---------------------------------------------------------------------------
DB_DIR = Path.home() / ".infrasim"
DB_PATH = DB_DIR / "infrasim.db"


def get_database_url(path: Path | None = None) -> str:
    """Return the async SQLite database URL."""
    p = path or DB_PATH
    return f"sqlite+aiosqlite:///{p}"


# ---------------------------------------------------------------------------
# Base model
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# ORM models (SQLAlchemy 2.0 mapped_column style)
# ---------------------------------------------------------------------------

class TeamRow(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[_dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )

    # relationships
    users: Mapped[list["UserRow"]] = relationship(back_populates="team")
    projects: Mapped[list["ProjectRow"]] = relationship(back_populates="team")


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )

    # relationships
    team: Mapped[TeamRow | None] = relationship(back_populates="users")
    projects: Mapped[list["ProjectRow"]] = relationship(back_populates="owner")


class ProjectRow(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[_dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    # relationships
    owner: Mapped[UserRow | None] = relationship(back_populates="projects")
    team: Mapped[TeamRow | None] = relationship(back_populates="projects")
    simulation_runs: Mapped[list["SimulationRunRow"]] = relationship(
        back_populates="project", cascade="all, delete-orphan",
    )


class SimulationRunRow(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id"), nullable=True,
    )
    engine_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="static",
    )
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    results_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False,
    )

    # relationships
    project: Mapped[ProjectRow | None] = relationship(back_populates="simulation_runs")


# ---------------------------------------------------------------------------
# Engine / session factory
# ---------------------------------------------------------------------------

_engine = None
_session_factory = None


def _get_engine(url: str | None = None):
    global _engine
    if _engine is None:
        db_url = url or get_database_url()
        _engine = create_async_engine(db_url, echo=False)
    return _engine


def get_session_factory(url: str | None = None) -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        engine = _get_engine(url)
        _session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return _session_factory


def reset_engine() -> None:
    """Reset engine and session factory (useful for tests)."""
    global _engine, _session_factory
    if _engine is not None:
        # We don't await dispose here; callers should do that if needed.
        _engine = None
    _session_factory = None


async def init_db(url: str | None = None) -> None:
    """Create all tables if they don't exist.

    Also ensures the database directory exists.
    """
    if url is None:
        DB_DIR.mkdir(parents=True, exist_ok=True)

    engine = _get_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
