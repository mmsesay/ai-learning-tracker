- **Python** → AI, agents, LLMs, RAG, ML, data processing, experimentation.
- **Go** → APIs, microservices, production backends, distributed systems, high-performance services.

That's exactly how many AI companies work today. Researchers and AI engineers prototype in Python, while backend services are often written in Go, Rust, Java, or TypeScript.

---

# Which project should you start with?

I'd change the order slightly now that your goal is becoming an **AI Engineer** rather than simply learning tool calling.

## Phase 1 — Foundations (Start Here)

### Project 1 — AI Terminal Assistant ⭐⭐⭐⭐⭐

**This is the one I'd start today.**

Goal:

Build a local CLI assistant that can use tools.

Example

```text
You:
Where is Redis configured?

Agent:
→ list_files()
→ search_text()
→ read_file()
→ answer
```

Tools to build one at a time

- list_files
- read_file
- search_text
- write_file
- execute_shell_command
- git_status

By the end you'll understand:

- Tool Calling
- JSON schemas
- Function execution
- Prompt engineering
- Agent loop
- Context management

This project alone teaches nearly every fundamental concept behind AI agents.

---



# Phase 2 — Local Coding Agent

After Terminal Assistant becomes useful...

Add:

- git diff
- git log
- run tests
- explain errors
- search codebase

Example

```text
Explain why the build failed.

→ run tests

→ inspect logs

→ search files

→ answer
```

Now you're approaching Cursor.

---



# Phase 3 — Ubuntu DevOps Agent

Since you're always working on Ubuntu.

Teach the agent

- Docker
- Kubernetes
- Memory usage
- CPU
- Open ports
- Processes

Example

```text
Why is my computer slow?

Agent

→ memory tool

→ cpu tool

→ docker tool

→ summarize
```

---



# Phase 4 — LEPA AI Assistant

Now build an AI specifically for your project.

Questions like

```text
Where are grades calculated?

How does authentication work?

Show all Redis usage.

Explain the notification service.
```

Later add

- Vector Search
- Embeddings
- Codebase indexing

This becomes your personal engineering assistant.

---



# Phase 5 — Transcript Intelligence

You've already worked on transcript injection.

Now make your own.

Tools

- Load transcript
- Summarize
- Extract action items
- Generate CRM notes
- Search conversations

Later add RAG.

---



# Phase 6 — PDF / Law Assistant

Since you're also studying law.

Load

- PDFs
- Notes
- Cases
- Books

Ask

```text
Summarize chapter 5.

Explain negligence.

Compare two cases.
```

---



# Phase 7 — Browser Agent

Playwright

Selenium

Browser Use

Examples

```text
Login

Click

Fill forms

Take screenshot

Extract text
```

Now you're learning autonomous agents.

---



# Phase 8 — Multi-Agent System

Now build

Manager Agent

↓

Coding Agent

↓

Research Agent

↓

Git Agent

↓

DevOps Agent

↓

Browser Agent

This is where real AI engineering becomes exciting.

---



# Phase 9 — Voice Agent

Speech

↓

LLM

↓

Tool Calls

↓

Speech

Jarvis.

---



# Phase 10 — Autonomous Developer

Eventually

```text
Fix my failing Docker deployment.

↓

Read logs

↓

Inspect Docker

↓

Inspect code

↓

Modify files

↓

Run tests

↓

Commit changes

↓

Explain everything
```

Congratulations.

You've basically built a miniature Claude Code.

---



# Learning Roadmap


| Phase | Project               | Main Concepts                             |
| ----- | --------------------- | ----------------------------------------- |
| 1     | AI Terminal Assistant | Tool Calling, JSON Schema, Agent Loop     |
| 2     | Coding Agent          | Code Understanding, Git, Shell            |
| 3     | DevOps Agent          | System Tools, Docker, Kubernetes          |
| 4     | LEPA Assistant        | RAG, Embeddings, Retrieval                |
| 5     | Transcript Agent      | Information Extraction, Summarization     |
| 6     | PDF/Law Assistant     | Document AI, Semantic Search              |
| 7     | Browser Agent         | Automation, Planning                      |
| 8     | Multi-Agent System    | Agent Coordination                        |
| 9     | Voice Agent           | Speech-to-Text, Text-to-Speech            |
| 10    | Autonomous Developer  | Long-running Agents, Planning, Reflection |


---



# Python Tech Stack I'd Recommend

Rather than jumping between frameworks, I'd keep a consistent stack:

- **Python 3.13+**
- **uv** for package management (much faster than pip)
- **Pydantic AI** for agent structure and tool definitions
- **LiteLLM** for connecting to multiple LLM providers
- **OpenRouter** for access to Claude, Gemini, and others
- **Typer** for building polished CLI applications
- **Rich** for beautiful terminal output
- **DuckDB** or **SQLite** for local storage
- **ChromaDB** (or FAISS later) for vector search
- **Playwright** when you reach browser automation

This stack is modern, lightweight, and close to what many AI startups use for agent development.

## A project document you can paste into Google Docs

---



# AI Engineering Project Roadmap



## Goal

Build practical AI agents from scratch while learning tool calling, agent loops, retrieval, planning, memory, and multi-agent systems. Every project should solve a real problem and be extensible into the next one.

## Principles

- Use **Python** for AI, LLMs, agents, RAG, and experimentation.
- Use **Go** for production APIs and backend services.
- Build locally first, then evolve projects into reusable tools.



## Project 1: AI Terminal Assistant

**Objective:** Learn tool calling by building a CLI assistant.

### Features

- List files
- Read files
- Search text
- Write files
- Execute shell commands
- Check Git status



### Concepts

- Tool calling
- Function schemas
- Agent loops
- Context management
- Error handling



## Project 2: AI Coding Assistant

**Objective:** Help understand and maintain codebases.

### Features

- Search code
- Explain functions
- Run tests
- Inspect Git history
- Diagnose build failures



### Concepts

- Code reasoning
- Multi-step tool usage
- Source code navigation



## Project 3: Ubuntu DevOps Assistant

**Objective:** Monitor and troubleshoot local systems.

### Features

- CPU and memory usage
- Disk space
- Running processes
- Open ports
- Docker containers
- Kubernetes inspection



### Concepts

- System automation
- Diagnostics
- Infrastructure tooling



## Project 4: LEPA AI Assistant

**Objective:** Build an AI expert for the LEPA codebase.

### Features

- Semantic code search
- Documentation search
- Architecture Q&A
- Vector search
- Embeddings



### Concepts

- RAG
- Embeddings
- Vector databases



## Project 5: Transcript Intelligence Agent

**Objective:** Analyze meeting and call transcripts.

### Features

- Summaries
- Action items
- Sentiment analysis
- CRM note generation
- Conversation search



### Concepts

- Information extraction
- Long-context prompting



## Project 6: PDF & Law Research Assistant

**Objective:** Query legal books and documents conversationally.

### Features

- PDF ingestion
- Semantic search
- Chapter summaries
- Citation lookup



### Concepts

- Document AI
- Retrieval pipelines



## Project 7: Browser Automation Agent

**Objective:** Control a browser using AI.

### Features

- Open websites
- Fill forms
- Extract data
- Take screenshots



### Concepts

- Browser automation
- Planning
- Tool orchestration



## Project 8: Multi-Agent System

**Objective:** Coordinate specialized agents.

### Agents

- Manager
- Coding
- Research
- DevOps
- Browser



### Concepts

- Delegation
- Agent communication
- Task decomposition



## Project 9: Voice Assistant

**Objective:** Build a voice-enabled AI assistant.

### Features

- Speech-to-text
- Tool calling
- Text-to-speech



### Concepts

- Real-time AI
- Conversational interfaces



## Project 10: Autonomous Developer

**Objective:** Create a coding agent capable of solving engineering tasks end-to-end.

### Features

- Diagnose issues
- Modify code
- Run tests
- Verify fixes
- Commit changes



### Concepts

- Autonomous planning
- Reflection
- Self-correction
- Long-running workflows

---

I think **Project 1 (AI Terminal Assistant)** is the perfect starting point. It's small enough to finish in a week or two, yet every improvement you make teaches a core AI engineering concept that carries directly into the later projects. Once it's stable, you'll have a reusable foundation that powers almost every subsequent project on your roadmap.