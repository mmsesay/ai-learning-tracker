# PRJ-01-B — DevAssist MCP

**DevAssist** is an MCP server that lists projects, searches code, and summarizes Git status under a configured `WORKSPACE_ROOT`.

It supports two transports:

| Transport | When | How |
|-----------|------|-----|
| **stdio** | Local Cursor / Claude Desktop | `TRANSPORT=stdio python server.py` |
| **Streamable HTTP** | Remote / Railway (default) | `python server.py` → `POST /mcp` |

This is the MCP sibling of **TAM** (PRJ-01-A): same “tools on your machine” idea, packaged for clients over MCP.

> **Note:** DevAssist is **Python** (official MCP Python SDK). Fastify/Express do not apply here — the SDK builds a **Starlette** ASGI app served by **uvicorn**, which is the recommended remote path for this stack.

## What is MCP?

**MCP (Model Context Protocol)** is a standard way for AI apps to connect to external tools.

- **stdio** — client spawns the server as a subprocess (local).
- **Streamable HTTP** — client calls a single HTTP endpoint (`/mcp`) over the network (remote). This replaces the older HTTP+SSE transport for new deployments.

## Architecture

```text
MCP Client (Cursor / AI SDK / Claude)
        │  HTTPS (or stdio locally)
        ▼
   DevAssist  GET /  ·  GET /health  ·  POST /mcp
        │
   MCPServer ("devassist")
        │
        ├── list_projects
        ├── search_code
        └── git_summary
              └── tools/*.py  (unchanged implementations)
```

## Available tools

| Tool | Purpose |
|------|---------|
| `list_projects()` | List first-level folders under `WORKSPACE_ROOT` |
| `search_code(query, project)` | Search source files (skips `.git`, `node_modules`, `.venv`, …) |
| `git_summary(project)` | Read-only branch + dirty files |

---

# Remote MCP Server

## What changed from the local version

- Default transport is **Streamable HTTP** on `HOST:PORT` with MCP at **`/mcp`**.
- Added **`GET /`** (service info) and **`GET /health`** (liveness).
- Optional **`API_KEY`** → `Authorization: Bearer <API_KEY>` on `/mcp`.
- **stdio** still works for local Cursor (`TRANSPORT=stdio`).
- Tool modules under `tools/` were **not** rewritten.

## Why Streamable HTTP?

It is the current MCP remote transport: one endpoint, works behind load balancers, and is what Cursor expects for `url`-based MCP entries. Legacy SSE exists only for older clients — DevAssist does not use it for the new remote path.

## Local Development

```bash
cd PRJ-01-B
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit WORKSPACE_ROOT / API_KEY as needed

export WORKSPACE_ROOT="$HOME/Projects"
export PORT=3000
export HOST=0.0.0.0
python server.py
```

Smoke checks:

```bash
curl -s http://127.0.0.1:3000/health
curl -s http://127.0.0.1:3000/
```

More curl / auth cases: [`TESTING.md`](TESTING.md).

### Local stdio (unchanged Cursor workflow)

```bash
TRANSPORT=stdio WORKSPACE_ROOT="$HOME/Projects" python server.py
```

`~/.cursor/mcp.json` example (stdio):

```json
{
  "mcpServers": {
    "devassist": {
      "command": "/ABS/PATH/PRJ-01-B/.venv/bin/python",
      "args": ["/ABS/PATH/PRJ-01-B/server.py"],
      "env": {
        "TRANSPORT": "stdio",
        "WORKSPACE_ROOT": "/ABS/PATH/Projects"
      }
    }
  }
}
```

## Environment variables

| Variable | Default | Meaning |
|----------|---------|---------|
| `PORT` | `3000` | Listen port (**Railway sets this**) |
| `HOST` | `0.0.0.0` | Bind address (required for Railway) |
| `TRANSPORT` | `streamable-http` | `streamable-http` or `stdio` |
| `WORKSPACE_ROOT` | `./demo_workspace` | Parent of projects (use `demo_workspace` on Railway) |
| `API_KEY` | _(empty)_ | **Required** when `HOST=0.0.0.0`. Bearer on `/mcp` |
| `MCP_ALLOWED_HOSTS` | _(empty)_ | Railway domain allowlist, e.g. `app.up.railway.app,app.up.railway.app:*` |

See [`.env.example`](.env.example). Never commit `.env`.

## Authentication

- **Public bind (`HOST=0.0.0.0`):** `API_KEY` is **required** (server exits otherwise).
- **Loopback (`HOST=127.0.0.1`):** `API_KEY` optional for open local HTTP.
- Clients send `Authorization: Bearer <API_KEY>` on `/mcp`.
- `/` and `/health` stay public for probes.

---

# Deployment

## Railway (recommended for this milestone)

Railway can deploy this Python app with Nixpacks (no Dockerfile required).

```text
1. Push this repo (or PRJ-01-B) to GitHub
2. Create a Railway project → Deploy from GitHub
3. Set Root Directory to PRJ-01-B (if the repo is the monorepo)
4. Configure variables (below)
5. Generate a public domain
6. Verify GET https://YOUR-RAILWAY-DOMAIN/health
7. Verify POST https://YOUR-RAILWAY-DOMAIN/mcp (with Bearer if API_KEY set)
8. Connect Cursor / AI SDK to https://YOUR-RAILWAY-DOMAIN/mcp
```

### Railway environment variables

| Variable | Example | Notes |
|----------|---------|--------|
| `PORT` | _(Railway)_ | Injected automatically — do not hard-code |
| `HOST` | `0.0.0.0` | Required so Railway can reach uvicorn |
| `TRANSPORT` | `streamable-http` | Default |
| `API_KEY` | long random secret | **Required** (server refuses public bind without it) |
| `WORKSPACE_ROOT` | `demo_workspace` | Ships with `sample-app`; Procfile inits git for demos |
| `MCP_ALLOWED_HOSTS` | `YOUR-APP.up.railway.app,YOUR-APP.up.railway.app:*` | Enable DNS rebinding allowlist once domain exists |

**Start command** (Procfile already does this):

```bash
python scripts/prepare_demo_workspace.py && python server.py
```

### Important Railway caveat

`WORKSPACE_ROOT` is a path **inside the container**, not your laptop. For the first demo, use the bundled `demo_workspace/` (one project: `sample-app`). Do not expect access to `~/Projects` on your machine.

---

# Connecting from Cursor

Remote Streamable HTTP ([Cursor MCP docs](https://cursor.com/docs/mcp)):

```json
{
  "mcpServers": {
    "devassist": {
      "url": "https://YOUR-RAILWAY-DOMAIN/mcp",
      "headers": {
        "Authorization": "Bearer ${env:DEVASSIST_API_KEY}"
      }
    }
  }
}
```

Local HTTP while developing:

```json
{
  "mcpServers": {
    "devassist-local-http": {
      "url": "http://127.0.0.1:3000/mcp",
      "headers": {
        "Authorization": "Bearer ${env:DEVASSIST_API_KEY}"
      }
    }
  }
}
```

Reload **Settings → Tools & MCP** after editing.

---

# Connecting from Claude Desktop

Claude Desktop historically prefers **stdio** local servers (`mcp install` / config `command`). For a **remote** URL, use a client that supports Streamable HTTP (Cursor, or an SDK). To keep using Claude Desktop locally:

```bash
TRANSPORT=stdio WORKSPACE_ROOT="$HOME/Projects" python server.py
```

and register that command in Claude’s MCP config (same idea as the stdio Cursor block above).

---

# Connecting from AI SDK

Small example under [`examples/ai-sdk-client/`](examples/ai-sdk-client/) using `@ai-sdk/mcp` + HTTP transport:

```ts
import { createMCPClient } from "@ai-sdk/mcp";

const mcpClient = await createMCPClient({
  transport: {
    type: "http",
    url: "https://YOUR-RAILWAY-DOMAIN/mcp",
    headers: { Authorization: `Bearer ${process.env.DEVASSIST_API_KEY}` },
  },
});

const tools = await mcpClient.tools();
// pass `tools` into generateText / streamText, then:
await mcpClient.close();
```

```bash
cd examples/ai-sdk-client
npm install
DEVASSIST_URL=https://YOUR-RAILWAY-DOMAIN/mcp \
DEVASSIST_API_KEY=your-key \
npm run list-tools
```

---

## Layout

```text
PRJ-01-B/
├── server.py              # tools + entry (stdio or HTTP)
├── config.py              # PORT / HOST / API_KEY / TRANSPORT
├── http_app.py            # / /health + Bearer middleware + Streamable HTTP app
├── tools/                 # list_projects, search_code, git_summary (unchanged)
├── tests/test_http.py
├── examples/ai-sdk-client/  # Vercel AI SDK consumer example
├── requirements.txt
├── Procfile
├── .env.example
├── TESTING.md
└── README.md
```

## Security

- Path jail under `WORKSPACE_ROOT` (existing).
- Tools are read-mostly (no mutating git).
- Set `API_KEY` on any public URL.
- Do not commit secrets.

## Phase 1 map

| ID | Focus |
|----|--------|
| **PRJ-01-A — TAM** | Tool calling inside your own CLI agent |
| **PRJ-01-B — DevAssist** | MCP server: local stdio → remote Streamable HTTP |
