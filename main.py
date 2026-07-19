"""AURA backend API — minimal FastAPI service for the mobile MVP.

Endpoints:
  POST /chat     — accept a user message, call the LLM, return AURA's reply
  GET  /context  — return recent conversations (stub until persistence is added)

Environment variables:
  OPENAI_API_KEY     — required for real LLM replies
  OPENAI_MODEL       — optional, defaults to gpt-4o-mini
  AURA_SYSTEM_PROMPT — optional override for the assistant persona
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from pydantic import BaseModel

app = FastAPI(title="AURA API", version="0.1.0")

# CORS — tighten allow_origins to your app domain in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SYSTEM_PROMPT = os.getenv(
    "AURA_SYSTEM_PROMPT",
    (
        "You are AURA, a persistent AI companion. "
        "You help the user stay organized, remember what matters, and make progress on their goals. "
        "Be calm, concise, proactive, and genuinely helpful. "
        "When the user shares something important, acknowledge that you will remember it. "
        "When relevant, gently connect the current message to their goals, schedule, or memories. "
        "Avoid generic filler; prefer practical, specific responses."
    ),
)

client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    conversationId: str
    message: str


class ChatResponse(BaseModel):
    reply: str


class Conversation(BaseModel):
    id: str
    title: str
    preview: str
    updatedAt: datetime


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    """Single-shot chat endpoint matching the Flutter app's current client.

    TODO: upgrade to SSE or WebSocket streaming once the mobile client
    supports incremental rendering.
    """
    if client is None:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured on the server.",
        )

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": payload.message},
            ],
            temperature=0.7,
            max_tokens=512,
        )
    except Exception as exc:  # noqa: BLE001 — surface as HTTP error for now
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}") from exc

    reply = response.choices[0].message.content or ""
    return ChatResponse(reply=reply)


@app.get("/context", response_model=List[Conversation])
async def get_context() -> List[Conversation]:
    """Return recent conversations.

    Stub implementation — swap in real persistence (SQLite/Postgres) once
    conversations are stored server-side.
    """
    now = datetime.now(timezone.utc)
    return [
        Conversation(
            id="c1",
            title="Planning tomorrow",
            preview="Let's move the gym session to 7:00…",
            updatedAt=now,
        ),
        Conversation(
            id="c2",
            title="Book recommendations",
            preview="Added two titles to your reading memory.",
            updatedAt=now,
        ),
    ]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
