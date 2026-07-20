"""GET /briefing — morning briefing composed from DB goals and events."""
from __future__ import annotations

import json
from datetime import datetime
from typing import List, Tuple

from fastapi import APIRouter
from sqlmodel import Session, select

import llm
from db import SessionDep
from models import BriefingOut, CalendarEvent, CalendarEventOut, Goal, GoalOut
from weather import weather_for

router = APIRouter(tags=["briefing"])


def today_items(session: Session) -> Tuple[List[CalendarEvent], List[Goal]]:
    """Today's calendar events (ordered) and goals due today."""
    today = datetime.now().date()
    events = [
        e for e in session.exec(select(CalendarEvent).order_by(CalendarEvent.start)).all()
        if e.start.date() == today
    ]
    goals = [
        g for g in session.exec(select(Goal).order_by(Goal.due_date, Goal.id)).all()
        if g.due_date is None or g.due_date.date() == today
    ]
    return events, goals


def _fmt_events(events: List[CalendarEvent]) -> str:
    return ", ".join(f"{e.start:%H:%M} {e.title}" for e in events) or "no meetings"


def _fmt_goals(goals: List[Goal]) -> str:
    return ", ".join(g.title for g in goals) or "no goals set"


def fallback_suggestions(events: List[CalendarEvent], goals: List[Goal]) -> List[str]:
    suggestions = [f"Prepare for {e.title} at {e.start:%H:%M}" for e in events[:2]]
    suggestions += [
        f"Make progress on: {g.title}" for g in goals if not g.is_completed
    ][: max(0, 3 - len(suggestions))]
    return suggestions or ["Take a moment to plan your day."]


def fallback_briefing(events: List[CalendarEvent], goals: List[Goal]) -> dict:
    open_goals = [g for g in goals if not g.is_completed]
    headline = f"{len(events)} meeting{'s' if len(events) != 1 else ''} and {len(open_goals)} open goal{'s' if len(open_goals) != 1 else ''} on deck for today"
    summary = (
        f"Today you have {_fmt_events(events)}. "
        f"Your goals: {_fmt_goals(goals)}."
    )
    return {
        "headline": headline,
        "summary": summary,
        "suggestions": fallback_suggestions(events, goals),
    }


async def llm_briefing(events: List[CalendarEvent], goals: List[Goal]) -> dict | None:
    """Generate headline/summary/suggestions via OpenAI, or None on any failure."""
    if llm.client is None:
        return None
    prompt = (
        "Compose a short morning briefing from this data. Reply with JSON only, "
        'with keys "headline" (short string), "summary" (1-2 sentences), and '
        '"suggestions" (list of 3 short actionable strings).\n'
        f"Meetings today: {_fmt_events(events)}.\n"
        f"Goals today: {_fmt_goals(goals)} "
        f"(completed: {', '.join(g.title for g in goals if g.is_completed) or 'none'})."
    )
    try:
        raw = await llm.complete(
            [{"role": "user", "content": prompt}], temperature=0.6, max_tokens=300
        )
        data = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        if not all(k in data for k in ("headline", "summary", "suggestions")):
            return None
        return data
    except Exception:  # noqa: BLE001 — any LLM/parse failure falls back to template
        return None


@router.get("/briefing", response_model=BriefingOut)
async def get_briefing(session: SessionDep) -> BriefingOut:
    today = datetime.now().date()
    events, goals = today_items(session)
    generated = await llm_briefing(events, goals) or fallback_briefing(events, goals)
    return BriefingOut(
        date=today.isoformat(),
        headline=generated["headline"],
        summary=generated["summary"],
        weather=weather_for(today),
        meetings=[CalendarEventOut.model_validate(e) for e in events],
        goals=[GoalOut.model_validate(g) for g in goals],
        suggestions=generated["suggestions"],
    )
