# Weather MCP (PRJ-01-B)

Phase 1 project **B**: a minimal **Model Context Protocol** server that exposes US weather tools to MCP clients (e.g. Cursor).

Built after **PRJ-01-A (TAM)** — same idea of tools, but served over MCP instead of a custom CLI agent loop.

## Tools

| Tool | What it does |
|------|----------------|
| `get_alerts` | Active weather alerts for a US state (`CA`, `NY`, …) |
| `get_forecast` | Short forecast for a latitude / longitude (NWS coverage) |

Data comes from the [National Weather Service API](https://www.weather.gov/documentation/services-web-api) (`api.weather.gov`). Outside the US, requests will fail or return nothing useful.

## Stack

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- `mcp[cli]` (MCP Python SDK) — `MCPServer` + stdio transport
- `httpx2` (pulled in by the SDK) for NWS HTTP calls

## Run locally

```bash
cd PRJ-01-B
uv sync
uv run weather.py
```

The process speaks MCP over **stdio** (what Cursor expects).

## Cursor MCP config

Example `~/.cursor/mcp.json` entry (adjust the path):

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/ai-learning-tracker/PRJ-01-B",
        "run",
        "weather.py"
      ]
    }
  }
}
```

Reload MCP in **Cursor Settings → Tools & MCP** after changing the path.

## Layout

| File | Role |
|------|------|
| `weather.py` | MCP server + `get_alerts` / `get_forecast` |
| `pyproject.toml` | Dependencies (`mcp[cli]`) |
| `main.py` | uv scaffold hello (unused by the MCP) |

## How it fits the roadmap

1. **PRJ-01-A** — tool calling inside your own agent loop  
2. **PRJ-01-B** — same skill surface, exposed as an MCP server other apps can call  

Next phases build on that pattern (more tools, richer servers, agents that consume MCP).
