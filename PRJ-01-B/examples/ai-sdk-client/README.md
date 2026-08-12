# AI SDK → remote DevAssist MCP

Minimal TypeScript example that connects the **Vercel AI SDK** to the deployed **DevAssist** MCP server over **Streamable HTTP**.

```text
User prompt
    ↓
AI SDK (generateText)
    ↓
MCP Client (@ai-sdk/mcp)
    ↓ HTTPS + Bearer
https://ai-learning-tracker-c7m5.onrender.com/mcp
    ↓
DevAssist tools (list_projects, search_code, git_summary)
```

This does **not** start a local MCP server. DevAssist stays on Render.

## Install

```bash
cd PRJ-01-B/examples/ai-sdk-client
npm install
```

## Environment

```bash
cp .env.example .env
```

Edit `.env`:

| Variable | Required | Purpose |
|----------|----------|---------|
| `DEVASSIST_URL` | no | Defaults to `https://ai-learning-tracker-c7m5.onrender.com/mcp` |
| `DEVASSIST_API_KEY` | **yes** | Same value as Render `API_KEY` (Bearer) |
| `OPENROUTER_API_KEY` **or** `OPENAI_API_KEY` | **yes** | Model for `generateText` |
| `OPENAI_BASE_URL` | no | Default OpenRouter: `https://openrouter.ai/api/v1` |
| `OPENAI_MODEL` | no | Default: `google/gemma-4-26b-a4b-it:free` (tool-capable) |

Never hard-code keys. Never commit `.env`.

## How MCP tools reach the model

1. `createMCPClient({ transport: { type: "http", url, headers } })` opens Streamable HTTP to Render.
2. `await mcpClient.tools({ schemas })` discovers DevAssist tools and converts them to AI SDK tools.
   - Explicit Zod `schemas` are used so zero-arg tools like `list_projects` validate correctly.
3. Each tool is lightly re-wrapped with `tool()` so `execute` returns plain text (easier for the model + avoids a CallToolResult/`toModelOutput` edge case).
4. `generateText({ model, tools, prompt, stopWhen })` lets the model call those tools over HTTPS.
5. `mcpClient.close()` cleans up the session.

## Run

List tools only (no LLM):

```bash
npm run list-tools
```

Full demo (model + tools):

```bash
npm start
```

Custom prompt:

```bash
npx tsx run.ts "List the projects available in my workspace."
npx tsx run.ts "Search sample-app for greet."
```

## Example prompts

- `List the projects available in my workspace.`
- `Search the sample-app project for TODO.`
- `What is the git status of sample-app?`
- `List projects, then search sample-app for greet.`

## Expected remote signal

Successful `list_projects` output from Render includes paths under:

```text
/opt/render/project/src/PRJ-01-B/demo_workspace
```

If you see only local paths like `/home/...`, you are not hitting Render.

## Notes

- Free Render instances may cold-start (first request can take ~30–60s).
- Keep `DEVASSIST_API_KEY` in sync with the Render dashboard `API_KEY`.
- OpenRouter Chat Completions (`.chat(modelId)`) is used so tool rounds stay reliable.
