# PRJ-02 — LEPA Support Agent

AI-powered **support workflow** for the fictional **LEPA School Management System**.

This is **Project 2** in the [ai-learning-tracker](https://github.com/mmsesay/ai-learning-tracker) series: a **LangGraph learning project**, not a production chatbot.

> Emphasis: **agent workflow** — state, routing, tools, memory, multi-agent split.

---

## Learning objectives

After reading this repo you should be able to explain:

| Concept | Demonstrated by |
|---------|-----------------|
| `StateGraph` + typed state | `app/state.py`, `app/graph.py` |
| `START` / `END` | Graph entry/exit |
| Conditional routing | `route_after_classify` + `add_conditional_edges` |
| Tool calling | `search_knowledge` over Markdown docs |
| Multi-agent orchestration | intake → knowledge → support |
| Checkpoint / conversation memory | SQLite `thread_id` in `app/memory/` |
| HTTP surface | FastAPI `POST /chat` |
| Graph visualization | Mermaid/ASCII via `app/visualize.py` |

---

## How this fits the series

```text
PRJ-01-A — TAM
Tool calling inside my own agent
        ↓
PRJ-01-B — DevAssist MCP
Tools as a standard protocol
        ↓
PRJ-01-C — Agent Harness
Orchestrating model + remote MCP tools
        ↓
PRJ-02 — LEPA Support Agent (LangGraph)
Workflow as an explicit graph
```

**PRJ-01-C** taught a loop/harness. **PRJ-02** asks: what changes when the workflow is a **graph** with named nodes, branches, and durable state?

---

## Architecture

```text
HTTP POST /chat
        ↓
LangGraph (compiled StateGraph)
        ↓
┌─────────────────────────────────────────────┐
│  START → intake → classify                  │
│              │                              │
│       clarification_needed?                 │
│         /              \                    │
│       yes               no                  │
│        ↓                 ↓                  │
│  ask_clarification   knowledge              │
│        ↓              (search_knowledge)    │
│       END                ↓                  │
│                      support → END          │
└─────────────────────────────────────────────┘
        ↓
SQLite checkpointer (per thread_id)
```

### Live graph export

Generated from the compiled graph (not hand-waved):

- [`docs/graph.mmd`](docs/graph.mmd) — Mermaid
- [`docs/graph.ascii`](docs/graph.ascii) — ASCII

Regenerate:

```bash
uv run python -m app.visualize
```

Or fetch from the API: `GET /graph`.

---

## Agent responsibilities

| Agent / node | Job |
|--------------|-----|
| **Intake** | Detect `user_role` when mentioned (teacher/admin) |
| **Classify** | Set `issue_category` + `clarification_needed` |
| **Ask clarification** | Ask which LEPA area / symptom when the request is vague |
| **Knowledge** | Call `search_knowledge`, fill `retrieved_documents` |
| **Support** | Turn retrieved Markdown into the final answer |

Classification is **heuristic** on purpose (deterministic tests, clear routing lesson). Swapping in an LLM classifier later does not require redrawing the graph.

Support answers are **template-composed from docs** by default (offline, grounded).
When `OPENROUTER_API_KEY` / `OPENAI_API_KEY` is set and `LEPA_USE_LLM=true`, the
support node may rewrite the same snippets into a shorter reply — still falling
back to the template if the LLM call fails.

---

## State

`SupportState` fields travel through every node:

- `messages` — chat transcript (`add_messages` reducer)
- `user_role`, `issue_category`, `clarification_needed`
- `clarification_question`, `retrieved_documents`, `final_answer`
- `conversation_summary` — reserved for later

Nodes return **partial updates**; LangGraph merges them.

---

## Tool: `search_knowledge`

Simple Markdown search under `knowledge/` (auth, students, attendance, grades, reports).

- No vector database
- No embeddings
- Lesson = **tool + graph**, not RAG quality

---

## Memory (checkpointing)

SQLite checkpointer (`LEPA_CHECKPOINT_PATH`, default `./data/checkpoints.sqlite`).

Same `thread_id` → prior state reloads → new user message appends → graph runs again.

That enables:

```text
Turn 1: "help"           → clarification question
Turn 2: "grades missing" → knowledge + support answer
```

---

## Running locally

```bash
cd PRJ-02
cp .env.example .env   # optional for Step 4–5; LLM not required yet
uv sync --extra dev
uv run pytest -q
uv run uvicorn api.main:app --reload --port 8000
```

### Example conversation

```bash
# Vague → clarify
curl -s http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"help"}'
```

```bash
# Same thread → grades path
curl -s http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Why aren'\''t grades showing?","thread_id":"PASTE_THREAD_ID"}'
```

Clear single-turn:

```bash
curl -s http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"How do I enter grades?"}'
```

---

## Project layout

```text
PRJ-02/
├── app/
│   ├── graph.py          # StateGraph wiring
│   ├── state.py          # SupportState
│   ├── visualize.py      # Mermaid / ASCII export
│   ├── settings.py
│   ├── agents/           # intake, knowledge, support
│   ├── nodes/            # classify, ask_clarification
│   ├── tools/            # search_knowledge
│   ├── memory/           # SQLite checkpointer
│   └── prompts/
├── knowledge/            # LEPA support Markdown
├── api/main.py           # FastAPI
├── docs/graph.mmd        # exported topology
└── tests/
```

---

## Build steps (how this repo grew)

| Step | Focus |
|------|--------|
| 1 | State + `START → node → END` |
| 2 | Intake, classify, conditional edges |
| 3 | Knowledge base + tool + support |
| 4 | FastAPI + SQLite memory |
| 5 | Graph visualization + educational README |
| 6 | Optional LLM support polish (fallback to template) |

---

## Future improvements (not implemented)

Extension points only — keep the core graph readable:

- LLM classifier (structured output) — support polish already optional
- Real RAG (embeddings + vector store)
- PostgreSQL / Redis checkpointers
- MCP tools (e.g. call DevAssist from PRJ-01-B)
- Human-in-the-loop approval nodes
- Observability (LangSmith / tracing)
- Multiple model providers beyond env config

---

## License / intent

Portfolio + learning artifact for AI engineering. Built to show **LangGraph mechanics** clearly.
