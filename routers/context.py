"""GET /context (conversations), GET /summary, GET /weather."""
from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter
from sqlmodel import select

import llm
from db import SessionDep
from models import ChatMessage, Conversation, ConversationOut, SummaryOut, WeatherOut
from routers.briefing import _fmt_events, _fmt_goals, today_items
from weather import weather_for

router = APIRouter(tags=["context"])


@router.get("/context", response_model=List[ConversationOut])
async def get_context(session: SessionDep) -> List[ConversationOut]:
    """All conversations, most recently active first, with a preview snippet."""
    conversations = session.exec(
        select(Conversation).order_by(Conversation.updated_at.desc())
    ).all()
    result: List[ConversationOut] = []
    for conv in conversations:
        last = session.exec(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conv.id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(1)
        ).first()
        preview = ""
        if last is not None:
            preview = last.content if len(last.content) <= 60 else last.content[:59] + "…"
        result.append(
            ConversationOut(id=conv.id, title=conv.title, preview=preview, updated_at=conv.updated_at)
        )
    return result


@router.get("/summary", response_model=SummaryOut)
async def get_summary(session: SessionDep) -> SummaryOut:
    """A "your day at a glance" sentence or two."""
    events, goals = today_items(session)
    done = [g.title for g in goals if g.is_completed]

    if llm.client is not None:
        prompt = (
            "Write a 'your day at a glance' summary in one or two sentences from "
            f"this data. Meetings: {_fmt_events(events)}. "
            f"Goals: {_fmt_goals(goals)}. Already done: {', '.join(done) or 'nothing yet'}."
        )
        try:
            text = await llm.complete(
                [{"role": "user", "content": prompt}], temperature=0.6, max_tokens=120
            )
            return SummaryOut(summary=text.strip())
        except Exception:  # noqa: BLE001 — fall back to template
            pass

    summary = (
        f"Today you have {len(events)} meeting{'s' if len(events) != 1 else ''} "
        f"({_fmt_events(events)}) and {len(goals)} goal{'s' if len(goals) != 1 else ''} to tackle. "
        f"Completed so far: {', '.join(done) or 'nothing yet'}."
    )
    return SummaryOut(summary=summary)


@router.get("/weather", response_model=WeatherOut)
async def get_weather() -> WeatherOut:
    return weather_for(datetime.now().date())
