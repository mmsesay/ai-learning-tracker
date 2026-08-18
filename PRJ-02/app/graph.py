"""LangGraph StateGraph for the LEPA Support Agent.

Step 4 graph (same topology as Step 3, now with optional checkpointing)
----------------------------------------------------------------------
START → intake → classify → (conditional)
                          ├─ clarify → ask_clarification → END
                          └─ continue → knowledge → support → END
"""

from __future__ import annotations

from typing import Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from app.agents.intake import run_intake
from app.agents.knowledge import run_knowledge
from app.agents.support import run_support
from app.nodes.ask_clarification import ask_clarification
from app.nodes.classify import classify_node
from app.state import SupportState


def route_after_classify(state: SupportState) -> Literal["clarify", "continue"]:
    """Conditional edge: clarification vs knowledge/support path."""
    if state.get("clarification_needed"):
        return "clarify"
    return "continue"


def build_graph(checkpointer: BaseCheckpointSaver | None = None):
    """Compile the support graph.

    Pass a checkpointer to enable multi-turn memory via ``thread_id``.
    """
    graph = StateGraph(SupportState)

    graph.add_node("intake", run_intake)
    graph.add_node("classify", classify_node)
    graph.add_node("ask_clarification", ask_clarification)
    graph.add_node("knowledge", run_knowledge)
    graph.add_node("support", run_support)

    graph.add_edge(START, "intake")
    graph.add_edge("intake", "classify")
    graph.add_conditional_edges(
        "classify",
        route_after_classify,
        {
            "clarify": "ask_clarification",
            "continue": "knowledge",
        },
    )
    graph.add_edge("ask_clarification", END)
    graph.add_edge("knowledge", "support")
    graph.add_edge("support", END)

    return graph.compile(checkpointer=checkpointer)


def get_app_graph():
    """Lazy singleton used by the API (with SQLite memory)."""
    from app.memory.checkpoint import get_sqlite_checkpointer

    return build_graph(checkpointer=get_sqlite_checkpointer())


# Default import for scripts/tests without persistence.
app_graph = build_graph()
