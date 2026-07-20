"""AURA backend API — FastAPI service for the mobile MVP.

Endpoints (see routers/ for details):
  POST /chat               — conversation-aware chat with persistence
  GET  /context            — conversations, most recent first
  GET  /goals              — goal list
  POST /goals/{id}/toggle  — flip a goal's isCompleted
  GET  /calendar           — calendar events
  GET  /memory             — memory items
  GET  /briefing           — morning briefing (LLM or template fallback)
  GET  /summary            — day-at-a-glance summary (LLM or fallback)
  GET  /weather            — deterministic weather stub
  GET  /health             — health check
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Dict, Optional

from dotenv import load_dotenv

load_dotenv()  # must run before local modules read env vars at import time

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlmodel import Session  # noqa: E402

from db import DB_URL, create_db_and_tables, engine, seed  # noqa: E402
from routers import briefing, calendar, chat, context, goals, memory  # noqa: E402

# Surfaced by /health so a broken DB connection is diagnosable without
# Vercel log access; startup stays alive even if the DB is unreachable.
_startup_error: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _startup_error
    try:
        create_db_and_tables()
        with Session(engine) as session:
            seed(session)
    except Exception as exc:  # noqa: BLE001 — reported via /health
        _startup_error = f"{type(exc).__name__}: {exc}"
    yield


app = FastAPI(title="AURA API", version="0.2.0", lifespan=lifespan)

# CORS — tighten allow_origins to your app domain in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(context.router)
app.include_router(goals.router)
app.include_router(calendar.router)
app.include_router(memory.router)
app.include_router(briefing.router)


@app.get("/health")
async def health() -> Dict[str, Optional[str]]:
    """Liveness + DB diagnostics (no secrets: scheme and host only)."""
    result: Dict[str, Optional[str]] = {
        "status": "ok",
        "db": DB_URL.split(":", 1)[0],
        "dbHost": DB_URL.split("@")[-1].split("/")[0] if "@" in DB_URL else None,
        "startupError": _startup_error,
    }
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        result["dbConnection"] = "ok"
    except Exception as exc:  # noqa: BLE001 — surface for debugging
        result["dbConnection"] = f"{type(exc).__name__}: {exc}"
    return result
