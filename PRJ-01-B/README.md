# PRJ-01-B — DevAssist MCP

**DevAssist** is an MCP server that lists projects, searches code, and summarizes Git status under a configured `WORKSPACE_ROOT`.

It supports two transports:

| Transport | When | How |
|-----------|------|-----|
| **stdio** | Local Cursor / Claude Desktop | `TRANSPORT=stdio python server.py` |
| **Streamable HTTP** | Remote / Render (default) | `python server.py` → `POST /mcp` |

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
| `PORT` | `3000` | Listen port (**Render sets `$PORT` — do not hard-code**) |
| `HOST` | `0.0.0.0` | Bind address (required on Render) |
| `TRANSPORT` | `streamable-http` | `streamable-http` or `stdio` |
| `WORKSPACE_ROOT` | `./demo_workspace` | Parent of projects (`demo_workspace` on Render) |
| `API_KEY` | _(empty)_ | **Required** when `HOST=0.0.0.0`. Bearer on `/mcp` |
| `MCP_ALLOWED_HOSTS` | _(empty)_ | Render domain allowlist, e.g. `app.onrender.com,app.onrender.com:*` |

See [`.env.example`](.env.example). Never commit `.env`.

## Authentication

- **Public bind (`HOST=0.0.0.0`):** `API_KEY` is **required** (server exits otherwise).
- **Loopback (`HOST=127.0.0.1`):** `API_KEY` optional for open local HTTP.
- Clients send `Authorization: Bearer <API_KEY>` on `/mcp`.
- `/` and `/health` stay public for probes.

---

# Deployment

## Render (Web Service)

Deploy DevAssist as a **Python 3** Web Service. No Docker.

```text
1. Push this repo to GitHub
2. Render → New → Web Service → connect the repo
3. Root Directory: PRJ-01-B
4. Runtime: Python 3
5. Build Command: pip install -r requirements.txt
6. Start Command: python server.py
7. Health Check Path: /health
8. Add environment variables (below)
9. Deploy → open https://YOUR-APP.onrender.com/health
10. Connect Cursor to https://YOUR-APP.onrender.com/mcp
```

### Render settings

| Setting | Value |
|---------|--------|
| **Root Directory** | `PRJ-01-B` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python server.py` |
| **Health Check Path** | `/health` |

`python server.py` reads `$PORT` from the environment (Render injects it) and binds `HOST` (default `0.0.0.0`). On startup it also prepares `demo_workspace/sample-app` as a tiny git repo when that folder is present.

### Render environment variables

| Variable | Value | Notes |
|----------|--------|--------|
| `HOST` | `0.0.0.0` | Required |
| `TRANSPORT` | `streamable-http` | Required |
| `PORT` | _(do not set)_ | Render provides `$PORT` |
| `API_KEY` | long random secret | **Required** |
| `WORKSPACE_ROOT` | `demo_workspace` | Bundled demo projects |
| `MCP_ALLOWED_HOSTS` | `YOUR-APP.onrender.com,YOUR-APP.onrender.com:*` | Set after you know the domain |

### Important Render caveat

`WORKSPACE_ROOT` is inside the Render service filesystem, not your laptop. Use the bundled `demo_workspace/` (`sample-app`) for the first demo.

---

# Connecting from Cursor

Remote Streamable HTTP ([Cursor MCP docs](https://cursor.com/docs/mcp)):

```json
{
  "mcpServers": {
    "devassist": {
      "url": "https://YOUR-APP.onrender.com/mcp",
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
    url: "https://YOUR-APP.onrender.com/mcp",
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
DEVASSIST_URL=https://YOUR-APP.onrender.com/mcp \
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
