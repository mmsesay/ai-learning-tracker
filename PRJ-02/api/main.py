"""FastAPI app — POST /chat for the LEPA Support Agent."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from app.graph import get_app_graph

app = FastAPI(
    title="LEPA Support Agent",
    description="PRJ-02 LangGraph learning API — school support workflow",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    """Incoming user message.

    ``thread_id`` ties turns together via the SQLite checkpointer. Omit it
    (or send empty) to start a new conversation thread.
    """

    message: str = Field(..., min_length=1)
    thread_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    category: str
    memory_updated: bool
    thread_id: str
    clarification_needed: bool = False


@app.get("/graph")
def graph_mermaid() -> dict[str, str]:
    """Return the live LangGraph topology as Mermaid (learning / docs)."""
    from app.visualize import mermaid_source

    return {"format": "mermaid", "source": mermaid_source()}


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    """Run one turn of the support graph.

    LangGraph memory: same ``thread_id`` → prior state (messages, role, …)
    is loaded, new HumanMessage is appended, graph runs again.
    """
    thread_id = (body.thread_id or "").strip() or str(uuid.uuid4())
    graph = get_app_graph()
    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(
        {"messages": [HumanMessage(content=body.message.strip())]},
        config=config,
    )

    return ChatResponse(
        answer=str(result.get("final_answer") or ""),
        category=str(result.get("issue_category") or "unknown"),
        memory_updated=True,
        thread_id=thread_id,
        clarification_needed=bool(result.get("clarification_needed")),
    )
