# PRJ-01-C — Testing

Run against the **remote** Render DevAssist MCP. Do not start the local Python server.

```bash
cd PRJ-01-C
cp .env.example .env   # set DEVASSIST_API_KEY + OPENROUTER_API_KEY
npm install
```

---

## Connection

```bash
npm run list-tools
```

Expect:

- Connects to `https://ai-learning-tracker-c7m5.onrender.com/mcp`
- Discovers `list_projects`, `search_code`, `git_summary`

Invalid credentials:

```bash
DEVASSIST_API_KEY=wrong npm run list-tools
```

Expect a clear harness/MCP error (not a hang, not a secret dump).

---

## Tools via agent

### list_projects

```bash
npm start "List the projects available in my workspace."
```

Expect: model calls `list_projects`; result mentions `sample-app` and ideally `/opt/render/`.

### search_code

```bash
npm start "Search sample-app for greet and summarize what you find."
```

Expect: `search_code` with `project=sample-app`, `query=greet`; matches in `app.py`.

### git_summary

```bash
npm start "Give me the Git status of sample-app."
```

Expect: `git_summary` for `sample-app`; branch/status text from the remote repo.

---

## Agent loop behavior

| Check | How |
|-------|-----|
| Final answer produced | CLI prints `Final answer:` |
| At least one tool | Step log shows `Model → <tool>` |
| Multiple steps | Multi-tool prompt shows several steps |
| Stops at MAX_STEPS | `MAX_STEPS=1 npm start "…"` should stop quickly |
| MCP client closes | Process exits cleanly after run (no hang) |
| Graceful errors | Bad key / network → `Harness error:` message |

Multi-step prompt:

```bash
npm start "Find the sample-app project, search it for greet, and explain what the matching code does."
```

---

## Remote evidence

Look for paths like:

```text
/opt/render/project/src/PRJ-01-B/demo_workspace
```

The CLI also prints `[ok] Tool output references /opt/render/` when present.

---

## Checklist (manual)

- [ ] Remote MCP connection succeeds
- [ ] Authentication succeeds
- [ ] Tools discovered
- [ ] `list_projects` works
- [ ] `search_code` works
- [ ] `git_summary` works
- [ ] Agent produces a final answer
- [ ] Agent executes at least one tool
- [ ] Agent can execute multiple steps
- [ ] Agent stops at `MAX_STEPS`
- [ ] Invalid credentials fail gracefully
- [ ] MCP client closes correctly
- [ ] Results come from Render (`/opt/render/`)
