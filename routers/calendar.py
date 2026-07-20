"""GET /calendar."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter
from sqlmodel import select

from db import SessionDep
from models import CalendarEvent, CalendarEventOut

router = APIRouter(tags=["calendar"])


@router.get("/calendar", response_model=List[CalendarEventOut])
async def list_events(session: SessionDep) -> List[CalendarEvent]:
    return list(session.exec(select(CalendarEvent).order_by(CalendarEvent.start)).all())
