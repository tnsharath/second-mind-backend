"""Shared OpenAI client and AURA persona.

``client`` is ``None`` when OPENAI_API_KEY is not configured — callers are
expected to fall back to deterministic behavior (or, for /chat, raise a 500).
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional

from openai import AsyncOpenAI

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

client: Optional[AsyncOpenAI] = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


async def complete(
    messages: List[Dict[str, str]],
    *,
    system: str = SYSTEM_PROMPT,
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> str:
    """Run a chat completion and return the assistant's text.

    Raises RuntimeError when no API key is configured; callers decide how to
    surface or fall back.
    """
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not configured on the server.")
    response = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "system", "content": system}, *messages],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""
