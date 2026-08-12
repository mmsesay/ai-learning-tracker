# PRJ-01-C — Agent Harness

Minimal TypeScript **agent harness** that orchestrates an LLM + remote **DevAssist** MCP tools so the **agent loop** is visible.

```text
User
 ↓
Agent Harness
 ↓
LLM
 ↓
tool call? ─── no ──→ final answer
 ↓ yes
MCP Client (HTTPS)
 ↓
Remote DevAssist on Render
 ↓
tool result → LLM → continue or final answer
```

This project intentionally avoids LangChain, LangGraph, CrewAI, AutoGen, Mastra, and the OpenAI Agents SDK. The goal is to see the primitives.

Do **not** start a local MCP server. Tools come from:

```text
https://ai-learning-tracker-c7m5.onrender.com/mcp
```

---

## What is an LLM?

A **large language model** predicts the next tokens given a prompt. Alone it can write and reason in text, but it cannot list your files or search a repo unless something else runs those actions.

## What is an agent?

An **agent** is an LLM plus a **goal-directed loop**: the model may choose to call tools, see results, and continue until it can answer. The intelligence is still the model; the usefulness comes from tools + iteration.

## What is an agent harness?

> The harness is the runtime/orchestration layer around the model that manages tools, state, execution, limits, errors, and the agent loop.

In this project the harness:

- loads config
- connects to remote MCP
- passes tools into `generateText`
- prints each step (model → tool → result)
- enforces `MAX_STEPS`
- closes the MCP session
- surfaces errors without leaking secrets

## Agent vs harness

| Concept | Role |
|---------|------|
| **LLM** | Intelligence / reasoning |
| **Agent** | Model + tools + goal-directed loop |
| **Harness** | Infrastructure that runs the agent |
| **Tool** | Capability the agent can invoke |
| **MCP** | Protocol for discovering/exposing tools |

## Agent loop

```text
User
 ↓
Harness
 ↓
LLM
 ↓
Tool call?
 ├── No → Final answer
 └── Yes
       ↓
    Execute tool (MCP over HTTPS)
       ↓
    Tool result
       ↓
      LLM
       ↓
    Continue (until final answer or MAX_STEPS)
```

### What the AI SDK does vs what the harness owns

| Layer | Responsibility |
|-------|----------------|
| **AI SDK (`generateText`)** | Sends messages + tool schemas to the model; when the model returns tool calls, runs each tool’s `execute`; appends tool results into the **in-memory** conversation; calls the model again |
| **`stopWhen: stepCountIs(N)`** | Ends the multi-step loop after at most **N** model steps |
| **Harness (`agent.ts` / `mcp.ts` / `index.ts`)** | Connects MCP, defines which tools exist, wraps MCP results as text, prints the visible loop, sets `MAX_STEPS`, handles errors, closes the client |

So: the SDK implements the mechanical “call model → run tools → append results” cycle. The harness decides *which* tools, *how* they connect, *how* the loop is shown, and *when* to stop for safety.

In-memory state for one run lives inside `generateText` (user prompt + intermediate tool messages). There is no database or long-term memory.

---

## Why not LangChain / etc.?

Frameworks hide the loop behind “agents” and graphs. That is useful in production later. Here we want the mechanics obvious: schemas, tool execute, step limit, MCP session lifecycle.

---

## How MCP fits

```text
Agent Harness
      ↓
    AI SDK
      ↓
   MCP Client (@ai-sdk/mcp)
      ↓ HTTPS + Bearer
Remote DevAssist (Render)
      ↓
list_projects / search_code / git_summary
```

---

## Learning comparison (PRJ-01)

| Project | Main lesson |
|---------|-------------|
| **PRJ-01-A — TAM** | Tool calling inside my own agent (local Python tools) |
| **PRJ-01-B — DevAssist** | Exposing tools through MCP (stdio → Streamable HTTP → Cursor / AI SDK) |
| **PRJ-01-C — Agent Harness** | Orchestrating the model/tool loop with remote MCP tools |

Together:

```text
PRJ-01-A: I can run tools the model asks for
PRJ-01-B: Tools can live behind a standard protocol on a remote server
PRJ-01-C: A harness wires model + remote tools into a visible agent loop
```

---

## Install

```bash
cd PRJ-01-C
npm install
cp .env.example .env
```

Edit `.env`:

| Variable | Required | Purpose |
|----------|----------|---------|
| `DEVASSIST_API_KEY` | yes | Same as Render `API_KEY` |
| `DEVASSIST_URL` | no | Defaults to Render `/mcp` |
| `OPENROUTER_API_KEY` | yes | Model provider |
| `OPENAI_MODEL` | no | Default tool-capable free model |
| `MAX_STEPS` | no | Default `6` |

Never hard-code or commit keys.

## Run

```bash
npm start "List the projects available in my workspace"
```

```bash
npm start "Search sample-app for greet and summarize what you find"
```

```bash
npm start "Give me the Git status of sample-app"
```

Discover tools only (no LLM):

```bash
npm run list-tools
```

More prompts: [`examples/prompts.md`](examples/prompts.md).

## Expected remote signal

Successful tool output from Render includes paths under:

```text
/opt/render/project/src/PRJ-01-B/demo_workspace
```

If you only see `/home/...`, you are not hitting Render.

## Layout

```text
PRJ-01-C/
├── src/
│   ├── agent.ts   # harness loop + visible step tracing
│   ├── mcp.ts     # remote DevAssist MCP client + tools
│   ├── config.ts  # env / MAX_STEPS
│   └── index.ts   # CLI
├── examples/
├── package.json
├── tsconfig.json
├── .env.example
├── README.md
└── TESTING.md
```

## Safety

- Secrets only from env; never printed
- Only DevAssist MCP tools (no arbitrary shell)
- `MAX_STEPS` hard stop
- MCP client always closed in `finally`
- Model / MCP errors reported without crashing silently
