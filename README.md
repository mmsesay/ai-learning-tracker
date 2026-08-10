# AI Learning Tracker

Public learning repo for **Maej** ([Muhammad Sesay](https://github.com/mmsesay)) — shipping small AI projects while leveling into AI engineering.

Personal study plans and daily logs live in **Google Sheets** (private). This repo is for **code you can clone**.

## Phase 1

| ID | Name | Status | Folder |
|----|------|--------|--------|
| PRJ-01-A | **TAM** — AI Terminal Assistant (tool calling CLI) | Done | [`PRJ-01-A/`](PRJ-01-A/) |
| PRJ-01-B | **Weather MCP** — NWS alerts & forecast via Model Context Protocol | Done | [`PRJ-01-B/`](PRJ-01-B/) |

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

## PRJ-01-B — Weather MCP

A small **MCP server** that exposes weather tools to clients like Cursor:

- `get_alerts` — active NWS alerts for a US state  
- `get_forecast` — forecast for a lat/lon (US / NWS coverage)  

```bash
cd PRJ-01-B
uv sync
uv run weather.py
```

Wire it into Cursor via MCP settings (stdio + `uv run weather.py`). Details: [`PRJ-01-B/README.md`](PRJ-01-B/README.md)

## Links

- Site: [maej.dev](https://maej.dev)  
- X: [@DeeMaejor](https://twitter.com/DeeMaejor)  
- OpenRouter: [openrouter.ai](https://openrouter.ai)  
- MCP: [modelcontextprotocol.io](https://modelcontextprotocol.io)
