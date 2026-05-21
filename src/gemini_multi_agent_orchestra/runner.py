"""Programmatic ADK Runner wrapper for the 3-agent orchestra.

The orchestra is a `SequentialAgent` (researcher → analyst → writer).
We collect every event so callers can inspect each sub-agent's turn,
then surface the writer's final text as the user-facing answer.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from typing import Any

from gemini_multi_agent_orchestra.agent import build_agent

try:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    _ADK_AVAILABLE = True
except ImportError:  # pragma: no cover
    _ADK_AVAILABLE = False


@dataclass
class AgentResponse:
    final_text: str
    events: list[dict[str, Any]]
    # Per-sub-agent last text. Keys: researcher / analyst / writer.
    by_author: dict[str, str] = field(default_factory=dict)
    error: str | None = None


async def _ainvoke(question: str, *, stub: bool, model: str) -> AgentResponse:
    agent = build_agent(model=model, stub=stub)
    if agent is None or not _ADK_AVAILABLE:
        return AgentResponse(
            final_text="(offline-fallback) google-adk not installed.",
            events=[], error="ADK not available",
        )
    session_service = InMemorySessionService()
    app_name = "gemini-multi-agent-orchestra"
    user_id = os.getenv("USER", "demo")
    session = await session_service.create_session(app_name=app_name, user_id=user_id)
    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)
    content = types.Content(role="user", parts=[types.Part(text=question)])
    events: list[dict[str, Any]] = []
    by_author: dict[str, str] = {}
    final_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=content):
        author = getattr(event, "author", None)
        is_final = event.is_final_response() if hasattr(event, "is_final_response") else False
        ev = {"author": author, "is_final": is_final}
        if hasattr(event, "content") and event.content is not None:
            parts = getattr(event.content, "parts", []) or []
            text = "".join(getattr(p, "text", "") or "" for p in parts)
            ev["text"] = text
            if text and author:
                # Keep the most recent text per sub-agent — final response
                # for that sub-agent overwrites any earlier streamed text.
                if is_final or author not in by_author:
                    by_author[author] = text
            # Writer is the last sub-agent in the sequence; its final
            # response is the orchestra's final answer.
            if is_final and author == "writer":
                final_text = text
            elif is_final and not final_text:
                # Fallback: any final response keeps us covered if author
                # naming changes.
                final_text = text
        events.append(ev)
    # If writer never emitted a final, fall back to whatever final text
    # we did see (e.g. analyst final if writer wasn't reached).
    if not final_text and by_author.get("writer"):
        final_text = by_author["writer"]
    return AgentResponse(final_text=final_text, events=events, by_author=by_author)


def ask(question: str, *, stub: bool = True, model: str = "gemini-2.5-flash") -> AgentResponse:
    return asyncio.run(_ainvoke(question, stub=stub, model=model))
