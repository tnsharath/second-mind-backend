"""GET /memory."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter
from sqlmodel import select

from db import SessionDep
from models import MemoryItem, MemoryItemOut

router = APIRouter(tags=["memory"])


@router.get("/memory", response_model=List[MemoryItemOut])
async def list_memory(session: SessionDep) -> List[MemoryItem]:
    return list(session.exec(select(MemoryItem).order_by(MemoryItem.timestamp.desc())).all())
