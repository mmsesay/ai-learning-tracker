# AI Terminal Assistant (TAM)

**TAM** is a local CLI AI agent. It uses **tool calling** to explore your workspace: list/read/search files, write (with confirmation), run shell (with confirmation), and check git status.

This is **PRJ-01-A** (Phase 1) on the AI engineering roadmap — built so you can read every step of the agent loop. Pair with **PRJ-01-B** (Weather MCP) for the MCP side of Phase 1.

## How TAM works

```text
You type a question in the terminal
        ↓
TAM sends your chat history + tool schemas to an LLM (via OpenRouter)
        ↓
The model may reply with tool_calls (e.g. list_files, search_text)
        ↓
TAM runs those Python functions on your machine
        ↓
Results go back to the model as tool messages
        ↓
Loop until the model answers in plain text
```

| File | Role |
|------|------|
| `config.py` | API key / model / workspace |
| `tools.py` | JSON schemas + Python tool implementations |
| `agent.py` | Agent loop (model ↔ tools) |
| `main.py` | Typer/Rich REPL (`tam` command) |

## Try it yourself (someone else)

They need: Python 3.10+, [uv](https://docs.astral.sh/uv/) (or pip), and a free [OpenRouter API key](https://openrouter.ai/keys).

```bash
# 1. Get the code
git clone https://github.com/mmsesay/ai-learning-tracker.git
cd ai-learning-tracker/PRJ-01-A

# 2. Configure
cp .env.example .env
# edit .env → set OPENROUTER_API_KEY=sk-or-v1-...

# 3. Install
uv venv && source .venv/bin/activate
uv pip install -e .

# 4. Run
tam
```

Then ask things like: `List the files here` or `Show git status`.

**Important:** do not share your `.env` — each person uses their own OpenRouter key. `.env` is gitignored.

## Setup (you already have the repo)

```bash
cd PRJ-01-A
cp .env.example .env
# edit .env and set OPENROUTER_API_KEY=...  (https://openrouter.ai/keys)

# Option A — uv (recommended)
uv venv && source .venv/bin/activate && uv pip install -e .

# Option B — pip + venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

If `python3 -m venv` fails on Ubuntu, install `python3.10-venv` (or use `uv`).

## Run

```bash
# short alias (recommended)
tam

# full name also works
terminal-assistant

# workspace is your current working directory
cd /path/to/some/project
tam
```

Commands inside the REPL: `quit` / `exit` / `q` to leave, `clear` to reset conversation history.

## Try these prompts

- `List the files here`
- `Search for TODO`
- `What does README.md say?`
- `Show git status`
- `Create a file called notes.txt with hello` (will ask to confirm)
- `Run: echo hello` (will ask to confirm)

## Provider: OpenRouter (free or paid models)

Defaults use OpenRouter free models:

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openrouter/free
```

`openrouter/free` auto-selects a free model that supports tool calling. Browse models: https://openrouter.ai/models?q=free

Pin a specific free model:

```env
OPENAI_MODEL=google/gemma-4-26b-a4b-it:free
```

Or switch to a paid model on the same key by changing `OPENAI_MODEL` only.
