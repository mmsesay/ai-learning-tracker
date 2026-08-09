# AI Learning Tracker

Public learning repo for **Maej** ([Muhammad Sesay](https://github.com/mmsesay)) — shipping small AI projects while leveling into AI engineering.

Personal study plans and daily logs live in **Google Sheets** (private). This repo is for **code you can clone** and articles you can follow.

## Projects

| ID | Name | Status | Folder |
|----|------|--------|--------|
| PRJ-01 | **TAM** — AI Terminal Assistant (tool calling CLI) | Done | [`PRJ-01/`](PRJ-01/) |
| Next | **MCP server** (Model Context Protocol) | Learning / next build | — |

## PRJ-01 — TAM

Local terminal agent that uses LLM **tool calling** to explore a workspace:

- list / read / search files  
- write files & run shell (with confirmation)  
- git status  
- OpenRouter free or paid models  

```bash
cd PRJ-01
cp .env.example .env   # set OPENROUTER_API_KEY
uv venv && source .venv/bin/activate
uv pip install -e .
tam
```

Full write-up: [`PRJ-01/MEDIUM-ARTICLE.md`](PRJ-01/MEDIUM-ARTICLE.md)

## What’s next (not built here yet)

After tool calling, the curriculum moves to **MCP** — exposing tools as a Model Context Protocol server so assistants like Cursor can call them the same way. That’s the next ice-breaker project after more MCP reading — not started in this repo yet.

## Links

- Site: [maej.dev](https://maej.dev)  
- X: [@DeeMaejor](https://twitter.com/DeeMaejor)  
- OpenRouter: [openrouter.ai](https://openrouter.ai)
