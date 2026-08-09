# I Built a Local AI Terminal Agent With Tool Calling (And You Can Too)

*How I built TAM — a CLI assistant that lists files, searches code, runs shell commands, and talks to free models on OpenRouter.*

---

I’m **Muhammad Sesay (Maej)** — a full-stack developer from Freetown, Sierra Leone, leveling into **AI engineering**.

After my first real lessons on **LLM tool calling**, I didn’t want another notebook demo. I wanted something I’d open in a real terminal. So I built **TAM** — **AI Terminal Assistant**.

TAM is a local CLI agent. You ask a question. It can call tools on your machine — list and read files, search text, write files (with your OK), run shell commands (with your OK), check git status — then answer using what it actually found.

**Code (public):** [github.com/mmsesay/ai-learning-tracker](https://github.com/mmsesay/ai-learning-tracker) → folder [`PRJ-01`](https://github.com/mmsesay/ai-learning-tracker/tree/main/PRJ-01)

This post is a short journey note plus a tutorial. You’ll leave knowing what TAM is, how the agent loop works, which models I used, and how to run or rebuild it.

---

## Why build this?

Chatbots talk. **Agents act.**

Tool calling is the bridge:

1. You describe tools with JSON schemas  
2. The model decides when to call them  
3. **Your code** runs the real functions  
4. You send results back into the chat  
5. The model answers with evidence, not guesses  

TAM is **Project 1** on my roadmap: small enough to finish, big enough to teach schemas, dispatch, the agent loop, context, and safety.

Everything later — coding agents, DevOps agents, RAG — sits on this same pattern.

---

## What it feels like

```bash
tam
```

Then:

- `List the files here`  
- `Search for TODO`  
- `What does README.md say?`  
- `Show git status`  
- `Create notes.txt with hello` → confirms `[y/N]`  
- `Run: echo hello` → confirms `[y/N]`  

You’ll see lines like:

```text
→ list_files({"path": "."})
→ search_text({"query": "TODO"})
```

That’s the loop, live — not magic.

---

## Stack (kept simple on purpose)

I skipped heavy agent frameworks for v1. I wanted to *see* every step.

| Piece | Choice | Why |
|-------|--------|-----|
| Language | Python 3.10+ | Default for AI prototyping |
| Install / CLI | `uv` + Typer | Fast setup, clean `tam` command |
| UI | Rich | Clear prompts and tool traces |
| LLM client | OpenAI Python SDK | Drop-in with OpenRouter |
| Provider | **OpenRouter** | Free + paid models, one key |
| Default model | `openrouter/free` | Picks a free model that supports tools |

Manual loop first. Frameworks later.

---

## What model did I use?

**OpenRouter** — not a paid OpenAI account.

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openrouter/free
```

### `openrouter/free`

OpenRouter’s **Free Models Router**. It selects a free model that supports what you need (including tool calling). Great for learning: real agent behavior, rate limits instead of a credit card.

### Pin a free model

```env
OPENAI_MODEL=google/gemma-4-26b-a4b-it:free
```

See what’s free today: [openrouter.ai/models?q=free](https://openrouter.ai/models?q=free)

### Go paid later

Same code. Same key. Change only the model id:

```env
OPENAI_MODEL=anthropic/claude-sonnet-4
```

Free while learning; paid when you need more quality. Free `:free` endpoints also rotate — if one dies, switch id or use `openrouter/free` again.

---

## How it works

```text
You type in the terminal
        ↓
main.py  (Typer + Rich REPL)
        ↓
agent.py → OpenRouter (Chat Completions + tools)
        ↓
   tool_calls?
    /        \
  yes         no → print final answer
   ↓
tools.py runs Python on your machine
   ↓
append role=tool result → call the model again
```

### REPL — `main.py`

A simple loop: Rich asks for input; `quit` / `clear` are special; everything else becomes `agent.run_turn(text)`.

### Tools — `tools.py`

Two halves:

- **`TOOL_SCHEMAS`** — JSON the *model* reads  
- **Python functions** — what *your computer* runs  

Tools: `list_files`, `read_file`, `search_text`, `write_file`, `execute_shell_command`, `git_status`.

Paths stay inside the **workspace** (folder where you launched `tam`). `../` escapes are blocked. Writes and shell need confirmation.

### Agent loop — `agent.py`

1. Append the user message  
2. `chat.completions.create(..., tools=TOOL_SCHEMAS, tool_choice="auto")`  
3. If there are `tool_calls`, run them and append `role: tool` results  
4. Call the model again  
5. When there’s no tool call, return the text  
6. Cap iterations so it can’t spin forever  

That loop *is* the agent. Frameworks wrap it. Build it by hand once.

---

## Layout

```text
PRJ-01/
  .env.example
  pyproject.toml          # exposes `tam`
  README.md
  src/terminal_assistant/
    config.py             # key, model, workspace
    tools.py              # schemas + functions
    agent.py              # the loop
    main.py               # CLI
```

---

## Run it yourself

**Need:** Python 3.10+, [uv](https://docs.astral.sh/uv/), free [OpenRouter key](https://openrouter.ai/keys).

```bash
git clone https://github.com/mmsesay/ai-learning-tracker.git
cd ai-learning-tracker/PRJ-01

cp .env.example .env
# set OPENROUTER_API_KEY=sk-or-v1-...

uv venv && source .venv/bin/activate
uv pip install -e .

tam
```

Try `List the files here` or `Show git status`.

Don’t commit `.env`. Use your own key.

Point it at another repo:

```bash
cd /path/to/some/project
tam
```

---

## Build the idea from scratch (learning path)

1. **One tool, no loop** — define `list_files`, call the API with `tools=[...]`, print `tool_calls`.  
2. **Dispatch** — parse arguments, run Python, print the result.  
3. **Close the loop** — append assistant + `role: tool` messages, call again for a text answer.  
4. **More tools + safety** — read/search, then write/shell with confirm + max iterations.  
5. **CLI** — Typer + Rich + a `tam` entry point.  

One concept at a time. That’s how TAM grew after the tools lesson.

---

## What I learned

1. The model doesn’t run tools — **your code** does.  
2. Schema quality changes tool-calling quality.  
3. Context is the message list; tool results must stay in it.  
4. Confirmations for write/shell are product features, not extras.  
5. OpenRouter made agent practice affordable while learning.

---

## What’s next

TAM (tool calling in a local agent) is done.

**Next on the curriculum: MCP — Model Context Protocol.**  
I’ll learn how to expose tools as an **MCP server** so clients like Cursor can call them the same way. That’s the ice-breaker after this article — **not built in the repo yet.** When I ship it, it’ll show up as the next project folder and (likely) another post.

Same foundations: tools, contracts, safety — just a standard way to plug them into other apps.

---

## Links

- Repo: [mmsesay/ai-learning-tracker](https://github.com/mmsesay/ai-learning-tracker)  
- TAM: [PRJ-01](https://github.com/mmsesay/ai-learning-tracker/tree/main/PRJ-01)  
- Me: [maej.dev](https://maej.dev) · [GitHub](https://github.com/mmsesay) · [X @DeeMaejor](https://twitter.com/DeeMaejor)  
- OpenRouter: [openrouter.ai](https://openrouter.ai)  
- MCP docs (next stop): [modelcontextprotocol.io](https://modelcontextprotocol.io)

If you build your own terminal agent, tell me what tool you added first.

— **Maej**

---

*Medium tags:* Artificial Intelligence, Python, LLM, AI Agents, Tutorial, Open Source, Machine Learning, Software Development
