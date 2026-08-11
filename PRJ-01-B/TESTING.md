# Manual testing guide — DevAssist remote MCP

## 1. Install & start (Streamable HTTP)

```bash
cd PRJ-01-B
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export WORKSPACE_ROOT="$HOME/Projects"   # or path that contains your repos
export PORT=3000
export HOST=0.0.0.0
# unset API_KEY for open local /mcp, or:
# export API_KEY=dev-secret

python server.py
```

Expect a log line like: `Starting DevAssist Streamable HTTP on http://0.0.0.0:3000/mcp`.

## 2. Health & service info

```bash
curl -s http://127.0.0.1:3000/ | jq .
curl -s http://127.0.0.1:3000/health | jq .
```

`/health` should return `{"status":"healthy",...}`.

## 3. MCP endpoint reachability

Without auth (API_KEY unset):

```bash
curl -s -i -X POST http://127.0.0.1:3000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'
```

You should **not** get HTTP 401. A JSON or SSE MCP initialize result is success.

## 4. Authentication

```bash
export API_KEY=dev-secret
# restart server.py

# Missing token → 401
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:3000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{}'

# Valid token → not 401
curl -s -i -X POST http://127.0.0.1:3000/mcp \
  -H 'Authorization: Bearer dev-secret' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'
```

`/` and `/health` stay public even when `API_KEY` is set.

## 5. Automated tests

```bash
pip install pytest httpx
pytest -q
```

## 6. Existing tools still registered

Use MCP Inspector or Cursor against `http://127.0.0.1:3000/mcp` and confirm:

- `list_projects`
- `search_code`
- `git_summary`

Or with stdio (unchanged local workflow):

```bash
TRANSPORT=stdio python server.py
```

## 7. Remote connection (after Render)

```bash
curl -s https://YOUR-APP.onrender.com/health
curl -s -i -X POST https://YOUR-APP.onrender.com/mcp \
  -H "Authorization: Bearer $API_KEY" \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'
```
