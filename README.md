# AI Learning Tracker

Public learning repo for **Maej** ([Muhammad Sesay](https://github.com/mmsesay)) — shipping small AI projects while leveling into AI engineering.

Personal study plans and daily logs live in **Google Sheets** (private). This repo is for **code you can clone**.

## Phase 1

| ID | Name | Status | Folder |
|----|------|--------|--------|
| PRJ-01-A | **TAM** — AI Terminal Assistant (tool calling CLI) | Done | [`PRJ-01-A/`](PRJ-01-A/) |
| PRJ-01-B | **DevAssist** — MCP server (list projects, search code, git status) | Done | [`PRJ-01-B/`](PRJ-01-B/) |

## PRJ-01-A — TAM

Local terminal agent that uses LLM **tool calling** to explore a workspace:

- list / read / search files  
- write files & run shell (with confirmation)  
- git status  
- OpenRouter free or paid models  

```bash
cd PRJ-01-A
cp .env.example .env   # set OPENROUTER_API_KEY
uv venv && source .venv/bin/activate
uv pip install -e .
tam
```

Details and setup: [`PRJ-01-A/README.md`](PRJ-01-A/README.md)

## PRJ-01-B — DevAssist MCP

**DevAssist** is a local **MCP server** Cursor can connect to:

- `list_projects` — projects under `WORKSPACE_ROOT`  
- `search_code` — search a project (skips `.git`, `node_modules`, `.venv`, …)  
- `git_summary` — read-only branch + dirty files  

```bash
cd PRJ-01-B
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Point Cursor MCP at `server.py` and set `WORKSPACE_ROOT`. Details: [`PRJ-01-B/README.md`](PRJ-01-B/README.md)

## Links

- Site: [maej.dev](https://maej.dev)  
- X: [@DeeMaejor](https://twitter.com/DeeMaejor)  
- OpenRouter: [openrouter.ai](https://openrouter.ai)  
- MCP: [modelcontextprotocol.io](https://modelcontextprotocol.io)
