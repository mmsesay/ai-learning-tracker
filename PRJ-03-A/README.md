# PRJ-03-A — AI Document Processing Pipeline

Part of the AI Learning Path — **Orchestration Tools**

A small, runnable pipeline that accepts a document, processes it asynchronously with **Temporal**, summarizes it with an **LLM** (or mock), and sends a completion email via **Trigger.dev** — without blocking the upload request.

> Deeper design notes: [`docs/pipeline-design.md`](docs/pipeline-design.md) · n8n notes: [`docs/n8n-experiment.md`](docs/n8n-experiment.md)

---

## What I'm Building

```text
Upload / Webhook
      ↓
Temporal DocumentProcessingWorkflow
      ├── extract text
      ├── analyze metadata
      └── AI summary
      ↓
Trigger.dev notification task
      ↓
Email (Resend or console)
```

Supported files for v1: **PDF** and **plain text**. No OCR.

---

## Why I Built It

To practice orchestration concepts in one vertical slice:

- durable workflows (Temporal)
- background tasks (Trigger.dev)
- webhooks as HTTP events
- async boundaries for long work
- retries / failure handling
- inserting AI as a **step**, not an agent

---

## Learning Objectives

After running this project you should be able to explain:

1. Why uploads return before processing finishes
2. Workflow vs activity (and determinism)
3. How Temporal stores progress as history
4. What Trigger.dev tasks are for
5. Why Temporal ≠ Trigger.dev ≠ n8n
6. Where an LLM fits inside orchestration
7. Basic idempotency for notifications

---

## Architecture

```text
                    DOCUMENT
                       │
                       ▼
                ┌──────────────┐
                │  Backend API │
                └──────┬───────┘
                       │
                       │ Start workflow
                       ▼
                ┌──────────────┐
                │   Temporal   │
                │   Workflow   │
                └──────┬───────┘
                       │
             ┌─────────┼──────────┐
             ▼         ▼          ▼
        Extract     Analyze   AI Summary
             │         │          │
             └─────────┼──────────┘
                       │
                       ▼
                ┌──────────────┐
                │ Trigger.dev  │
                │ Async Task   │
                └──────┬───────┘
                       │
                       ▼
                    📧 Email
```

---

## How the Pipeline Works

1. `POST /documents` validates and stores the file under `storage/uploads/`.
2. A JSON metadata record is written (`RECEIVED`).
3. The API starts `DocumentProcessingWorkflow` and returns `202` + `documentId`.
4. The Temporal worker extracts text, analyzes it, and calls the LLM (or mock).
5. An activity enqueues Trigger.dev `process-document-notification` (or local fallback).
6. Email is sent / logged; `GET /documents/:id` shows status and results.

---

## Why Temporal?

Temporal owns the **multi-step processing lifecycle**:

- durable state across crashes
- activity retries for transient failures
- clear separation: deterministic workflow vs side-effect activities

---

## Why Trigger.dev?

Trigger.dev owns **notification delivery** after processing results exist.

| | Temporal activity | Trigger.dev task |
|--|-------------------|------------------|
| Role here | Orchestrated processing steps | Background email delivery |
| History | Part of workflow event history | Separate task run |
| Best for | Ordered business pipeline | Fire-and-forget side effects |

They are **not competitors** in this design: one orchestrates the document job; the other delivers the completion notice asynchronously.

If you removed Trigger.dev, email could be a Temporal activity. We keep both so the learning project shows each tool’s job clearly.

---

## Why Webhooks?

A webhook is an HTTP endpoint another system can call when an event happens.

`POST /webhooks/document` downloads a remote file (learning-only) and starts the **same** Temporal workflow.

---

## Where n8n Fits

n8n is useful for visual automation around systems (forms → API → Slack/Sheets). See [`docs/n8n-experiment.md`](docs/n8n-experiment.md).

---

## Why n8n Is Not in the Core Pipeline

This project teaches code-level orchestration. n8n is explored separately so it does not hide Temporal/Trigger.dev mechanics.

---

## AI Processing

The LLM step returns structured JSON:

- `summary`
- `keyPoints`
- `topics`
- `category`

This is a normal completion call — **not** an agent with tools/planning.

If `LLM_API_KEY` is empty, mock mode returns a predictable summary so demos still work.

---

## Document States

`RECEIVED` → `PROCESSING` → `EXTRACTING` → `ANALYZING` → `SUMMARIZING` → `NOTIFYING` → `COMPLETED` / `FAILED`

---

## Failure and Retry Handling

| Case | What happens |
|------|----------------|
| Bad upload | `400`, no workflow |
| Temporal unavailable | `503` |
| Empty/scanned PDF | Non-retryable failure → `FAILED` (no OCR) |
| Transient LLM errors | Temporal activity retries (3 attempts) |
| Email failures | Trigger.dev task retries |
| Duplicate notify | Skipped via `notificationSentAt` |

**Retry:** flaky network / LLM / email.  
**Do not retry:** validation errors, unsupported types, empty extractable text.

---

## Idempotency

`notificationSentAt` is written only after a successful email send. Retries that would re-send are skipped.

---

## Project Structure

```text
PRJ-03-A/
├── src/
│   ├── server.ts / app.ts / worker.ts / config.ts
│   ├── routes/documents.ts
│   ├── routes/webhooks.ts
│   ├── workflows/documentProcessing.workflow.ts
│   ├── activities/document.activities.ts
│   ├── services/   # document, extraction, analysis, ai, email, notification
│   ├── store/documentStore.ts
│   ├── temporal/client.ts
│   └── types/document.ts
├── trigger/notifyDocumentProcessed.ts
├── docs/pipeline-design.md
├── docs/n8n-experiment.md
├── samples/temporal-notes.txt
├── storage/uploads/  storage/meta/
└── tests/
```

---

## Local Setup

```bash
cd PRJ-03-A
cp .env.example .env
npm install
```

Install Temporal CLI once: https://docs.temporal.io/cli#install  
(Linux installer: `curl -sSf https://temporal.download/cli.sh | sh`)

Optional:

- Trigger.dev project ref in `trigger.config.ts` + `TRIGGER_SECRET_KEY`
- `LLM_API_KEY` for real summaries
- `EMAIL_API_KEY` for Resend

---

## Environment Variables

See [`.env.example`](.env.example). Important ones:

| Variable | Purpose |
|----------|---------|
| `TEMPORAL_ADDRESS` | `localhost:7233` |
| `TEMPORAL_TASK_QUEUE` | `document-processing` |
| `TRIGGER_SECRET_KEY` | optional; empty → local notification fallback |
| `LLM_API_KEY` | optional; empty → mock AI |
| `LLM_BASE_URL` / `LLM_MODEL` | OpenAI-compatible endpoint |
| `EMAIL_API_KEY` / `EMAIL_FROM` / `EMAIL_TO` | Resend or console |

---

## Running Temporal

```bash
temporal server start-dev
```

UI: http://localhost:8233

---

## Running the API

```bash
npm run start:worker   # terminal 2
npm run start:api      # terminal 3
```

---

## Running Trigger.dev

```bash
npm run trigger:dev    # terminal 4 (optional)
```

Without Trigger.dev credentials, notifications still run via local async fallback.

---

## Processing a Document

```bash
curl -s http://localhost:3000/documents \
  -F "file=@samples/temporal-notes.txt"
```

```bash
curl -s http://localhost:3000/documents/DOC_ID | jq
```

Webhook example (public URL to a `.txt`/`.pdf`):

```bash
curl -s http://localhost:3000/webhooks/document \
  -H 'Content-Type: application/json' \
  -d '{"documentUrl":"https://example.com/file.txt","source":"external-system"}'
```

---

## Testing

```bash
npm test
npm run typecheck
```

---

## Example Output

Upload response:

```json
{
  "success": true,
  "message": "Document accepted for processing",
  "documentId": "doc_ab12cd34ef56"
}
```

Console email (fallback):

```text
========================================
EMAIL NOTIFICATION
========================================
Subject: Document Processing Complete: temporal-notes.txt
...
========================================
```

---

## What I Learned

Use this checklist before writing your article:

- [ ] Async upload vs waiting on AI/email
- [ ] Temporal workflow / activity / worker / history
- [ ] Trigger.dev background notification
- [ ] Webhook as HTTP event door
- [ ] n8n as adjacent automation, not core
- [ ] LLM as a pipeline step, not an agent
- [ ] Retries vs non-retryable extraction failures
- [ ] Simple notification idempotency

*(Long-form write-ups live in the private Maej Library; publish to Medium from there after you run the demos.)*

---

## Limitations

- Local JSON metadata (not a production DB)
- No OCR / scanned PDF support
- Webhook download has no auth
- Trigger.dev still needs a cloud project for “real” task runs
- Email provider support is Resend + console only
