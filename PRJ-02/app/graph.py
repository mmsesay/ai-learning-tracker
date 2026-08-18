"""LangGraph StateGraph for the LEPA Support Agent.

Step 1 scaffold: START → receive_question → END.

Later steps will add intake / classify / clarify / knowledge / support nodes
and conditional edges. Keeping the first graph tiny makes the core concepts
obvious before multi-agent complexity lands.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from app.state import SupportState


def receive_question(state: SupportState) -> dict:
    """Echo node — proves state flows START → node → END.

    LangGraph concept: a **node** is a function ``(state) -> partial_update``.
    We do not mutate ``state`` in place; we return the fields to merge.
    """
    messages: list[BaseMessage] = list(state.get("messages") or [])
    last_user = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user = str(msg.content)
            break

    stub = (
        "[scaffold] Graph received your message. "
        f"Next steps will classify and answer it. You said: {last_user!r}"
    )
    return {
        "final_answer": stub,
        "messages": [AIMessage(content=stub)],
        "issue_category": "unknown",
        "clarification_needed": False,
    }


def build_graph():
    """Compile the Step-1 teaching graph.

    LangGraph concepts demonstrated here
    ------------------------------------
    * ``StateGraph(SupportState)`` — typed state container
    * ``add_node`` — register a unit of work
    * ``START`` / ``END`` — explicit entry and exit
    * ``add_edge`` — unconditional transition
    * ``compile()`` — produce a runnable graph
    """
    graph = StateGraph(SupportState)

    graph.add_node("receive_question", receive_question)

    # START → receive_question → END  (linear path for step 1)
    graph.add_edge(START, "receive_question")
    graph.add_edge("receive_question", END)

    return graph.compile()


# Module-level compiled graph for simple imports in later API / CLI steps.
app_graph = build_graph()
