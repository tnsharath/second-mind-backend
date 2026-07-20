"""SQLModel database tables and API response schemas.

Response schemas use a camelCase alias generator so JSON keys match the
Flutter freezed client exactly (e.g. ``isCompleted``, ``updatedAt``).
Datetimes are stored as naive local time and serialized as ISO 8601 strings.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from sqlmodel import Field, SQLModel


# ---------------------------------------------------------------------------
# Database tables
# ---------------------------------------------------------------------------

class Conversation(SQLModel, table=True):
    id: str = Field(primary_key=True)
    title: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: str = Field(foreign_key="conversation.id", index=True)
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.now)


class Goal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    is_completed: bool = False
    due_date: Optional[datetime] = None


class CalendarEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    start: datetime
    end: Optional[datetime] = None
    location: Optional[str] = None


MEMORY_CATEGORIES = ("event", "goal", "preference", "note", "milestone")


class MemoryItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    category: str  # one of MEMORY_CATEGORIES
    timestamp: datetime = Field(default_factory=datetime.now)
    is_important: bool = False


# ---------------------------------------------------------------------------
# API schemas (camelCase JSON keys)
# ---------------------------------------------------------------------------

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )


class ChatRequest(CamelModel):
    conversation_id: str
    message: str


class ChatResponse(CamelModel):
    reply: str


class ConversationOut(CamelModel):
    id: str
    title: str
    preview: str
    updated_at: datetime


class GoalOut(CamelModel):
    id: int
    title: str
    is_completed: bool
    due_date: Optional[datetime] = None


class CalendarEventOut(CamelModel):
    id: int
    title: str
    start: datetime
    end: Optional[datetime] = None
    location: Optional[str] = None


class MemoryItemOut(CamelModel):
    id: int
    title: str
    description: str
    category: str
    timestamp: datetime
    is_important: bool


class WeatherOut(CamelModel):
    temperature_c: float
    condition: str
    high_c: float
    low_c: float


class BriefingOut(CamelModel):
    date: str
    headline: str
    summary: str
    weather: WeatherOut
    meetings: List[CalendarEventOut]
    goals: List[GoalOut]
    suggestions: List[str]


class SummaryOut(CamelModel):
    summary: str
