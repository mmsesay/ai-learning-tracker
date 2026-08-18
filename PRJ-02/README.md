# PRJ-02 — LEPA Support Agent

> **Status:** Step 1 scaffold only (state + minimal LangGraph).  
> Product name: **LEPA Support Agent** — support workflow for the LEPA School Management System.

This is a **LangGraph learning project**, not a production chatbot.

## Learning goals (full project)

- LangGraph `StateGraph`, state, `START` / `END`
- Conditional routing
- Tool calling
- Conversation memory (checkpointing)
- Multi-agent orchestration (intake → knowledge → support)
- Structured outputs
- Clean, readable architecture

## Step 1 (this commit slice)

Implemented:

- Project layout under `PRJ-02/`
- `SupportState` (`app/state.py`)
- Tiny graph: `START → receive_question → END` (`app/graph.py`)

Not yet: agents, tools, knowledge base, FastAPI, checkpointing, conditional edges.

## Target workflow (later steps)

```text
START
  → Intake / classify
  → Need clarification? ──yes──→ ask → (user reply) → classify again
  → no
  → Knowledge agent + search_knowledge tool
  → Support agent (final answer)
  → memory / END
```

## Roadmap in this series

```text
PRJ-01-A  Tool calling (TAM)
PRJ-01-B  MCP (DevAssist)
PRJ-01-C  Agent harness
PRJ-02    LangGraph — LEPA Support Agent   ← you are here
```

## Run Step 1 smoke check

```bash
cd PRJ-02
uv sync
uv run python -c "
from langchain_core.messages import HumanMessage
from app.graph import app_graph
out = app_graph.invoke({'messages': [HumanMessage(content='How do I enter grades?')]})
print(out['final_answer'])
"
```

## Next step (after your confirmation)

Wire **intake + classify + conditional routing** (clarification vs knowledge path).
