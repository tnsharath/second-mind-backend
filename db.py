"""Database engine, session dependency, and demo seed data."""
from __future__ import annotations

import os
from datetime import datetime, time, timedelta
from typing import Annotated, Iterator

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine, select

import models  # noqa: F401 — register tables on SQLModel.metadata
from models import CalendarEvent, Goal, MemoryItem

# Database URL resolution, in priority order:
#   1. AURA_DB_URL          — explicit override (local dev, hosted DB)
#   2. POSTGRES_URL         — injected by the Vercel–Supabase integration
#   3. SQLite fallback      — ./aura.db locally, /tmp on Vercel (read-only
#                             serverless filesystem; ephemeral per instance)
def _resolve_db_url() -> str:
    url = os.getenv("AURA_DB_URL") or os.getenv("POSTGRES_URL")
    if url:
        # SQLAlchemy requires the "postgresql://" scheme; Supabase/Vercel
        # may provide the legacy "postgres://" spelling.
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        return url
    return "sqlite:////tmp/aura.db" if os.getenv("VERCEL") else "sqlite:///./aura.db"


DB_URL = _resolve_db_url()
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
# Serverless (Vercel) creates a fresh engine per instance; keep the pool
# small so we don't exhaust Supabase's connection limit.
engine = create_engine(DB_URL, connect_args=connect_args, pool_size=2, max_overflow=1)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def _today_at(hour: int, minute: int = 0) -> datetime:
    return datetime.combine(datetime.now().date(), time(hour, minute))


def seed(session: Session) -> None:
    """Insert starter content mirroring the app's current mock data.

    Only fills tables that are completely empty, so user data is never
    overwritten. Datetimes are relative to "today" so demo data always
    lands on the current day.
    """
    now = datetime.now()

    if session.exec(select(Goal)).first() is None:
        session.add_all([
            Goal(title="Morning walk", due_date=_today_at(8, 0)),
            Goal(title="Finish proposal draft", due_date=_today_at(17, 0)),
            Goal(title="Read 15 pages", due_date=_today_at(21, 0)),
            Goal(title="Call mom", due_date=_today_at(19, 0)),
        ])

    if session.exec(select(CalendarEvent)).first() is None:
        session.add_all([
            CalendarEvent(
                title="Team standup",
                start=_today_at(10, 30),
                end=_today_at(11, 0),
                location="Zoom",
            ),
            CalendarEvent(
                title="Design review",
                start=_today_at(14, 0),
                end=_today_at(15, 0),
                location="Meeting room 2",
            ),
            CalendarEvent(
                title="Gym session",
                start=_today_at(18, 30),
                end=_today_at(19, 30),
                location="FitLife Gym",
            ),
        ])

    if session.exec(select(MemoryItem)).first() is None:
        session.add_all([
            MemoryItem(
                title="Prefers concise updates",
                description="The user likes short, bullet-point summaries over long paragraphs.",
                category="preference",
                timestamp=now - timedelta(days=2),
                is_important=True,
            ),
            MemoryItem(
                title="Sister's birthday dinner",
                description="Dinner at Bella Vita last Saturday; the user promised to call mom more often.",
                category="event",
                timestamp=now - timedelta(days=1),
            ),
            MemoryItem(
                title="Shipped first AURA prototype",
                description="The Flutter app talked to the backend for the first time.",
                category="milestone",
                timestamp=now - timedelta(days=3),
                is_important=True,
            ),
            MemoryItem(
                title="Book list",
                description="Wants to read 'Deep Work' and 'The Creative Act' next.",
                category="note",
                timestamp=now - timedelta(hours=5),
            ),
            MemoryItem(
                title="Q3 fitness target",
                description="Run 5 km three times a week; gym sessions are on the calendar.",
                category="goal",
                timestamp=now - timedelta(days=4),
                is_important=True,
            ),
            MemoryItem(
                title="Coffee order",
                description="Flat white, oat milk — usual order at the corner café.",
                category="note",
                timestamp=now - timedelta(hours=8),
            ),
        ])

    session.commit()
