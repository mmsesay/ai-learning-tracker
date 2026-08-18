"""Shared graph state for the LEPA Support Agent.

In LangGraph, **state** is the single object that flows through every node.
Each node reads fields it needs and returns a *partial update* that LangGraph
merges back into the state.

We use ``TypedDict`` + ``Annotated`` reducers — current LangGraph best practice
for message lists (append) vs scalar fields (overwrite).
"""

from __future__ import annotations

from typing import Annotated, Literal, NotRequired, TypedDict

from langgraph.graph.message import add_messages


IssueCategory = Literal[
    "authentication",
    "students",
    "attendance",
    "grades",
    "reports",
    "unknown",
]


class SupportState(TypedDict):
    """State that travels through the support graph.

    Fields
    ------
    messages:
        Full chat transcript. ``add_messages`` *appends* new messages instead
        of replacing the list — this is how LangGraph implements turn memory
        inside a single thread.
    user_role:
        Teacher / admin / unknown — filled by intake when detectable.
    issue_category:
        Coarse intent label used by conditional routing.
    clarification_needed:
        When True, the graph routes to the clarification node instead of
        knowledge search.
    clarification_question:
        The question we ask the user when details are missing.
    retrieved_documents:
        Snippets returned by ``search_knowledge`` (plain text for now — not RAG).
    final_answer:
        Last assistant reply ready for the API / CLI.
    conversation_summary:
        Optional short summary for longer threads (filled later; empty in step 1).
    """

    messages: Annotated[list, add_messages]
    user_role: NotRequired[str]
    issue_category: NotRequired[IssueCategory]
    clarification_needed: NotRequired[bool]
    clarification_question: NotRequired[str]
    retrieved_documents: NotRequired[list[str]]
    final_answer: NotRequired[str]
    conversation_summary: NotRequired[str]
