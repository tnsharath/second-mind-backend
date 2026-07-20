"""POST /chat — persisted, conversation-aware chat."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException
from sqlmodel import select

import llm
from db import SessionDep
from models import ChatMessage, ChatRequest, ChatResponse, Conversation

router = APIRouter(tags=["chat"])

HISTORY_LIMIT = 20


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, session: SessionDep) -> ChatResponse:
    conversation_id = payload.conversation_id or uuid.uuid4().hex

    conversation = session.get(Conversation, conversation_id)
    if conversation is None:
        title = payload.message if len(payload.message) <= 40 else payload.message[:39] + "…"
        conversation = Conversation(id=conversation_id, title=title)
        session.add(conversation)

    session.add(ChatMessage(conversation_id=conversation_id, role="user", content=payload.message))
    conversation.updated_at = datetime.now()
    session.commit()

    if llm.client is None:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured on the server.",
        )

    history: List[ChatMessage] = list(
        session.exec(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(HISTORY_LIMIT)
        ).all()
    )
    history.reverse()
    messages = [{"role": m.role, "content": m.content} for m in history]

    try:
        reply = await llm.complete(messages)
    except Exception as exc:  # noqa: BLE001 — surface as HTTP error for now
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}") from exc

    session.add(ChatMessage(conversation_id=conversation_id, role="assistant", content=reply))
    conversation.updated_at = datetime.now()
    session.commit()

    return ChatResponse(reply=reply)
