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

from dotenv import load_dotenv

load_dotenv()  # must run before local modules read env vars at import time

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from sqlmodel import Session  # noqa: E402

from db import create_db_and_tables, engine, seed  # noqa: E402
from routers import briefing, calendar, chat, context, goals, memory  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        seed(session)
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
async def health() -> dict[str, str]:
    return {"status": "ok"}
