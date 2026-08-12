/**
 * Agent harness: orchestrate LLM ↔ tool loop against remote DevAssist.
 *
 * The harness owns connection lifecycle, step limits, visible tracing, and
 * error boundaries. The LLM provides reasoning; MCP tools provide capabilities.
 */

import { createOpenAI } from "@ai-sdk/openai";
import { generateText, stepCountIs } from "ai";

import type { HarnessConfig } from "./config.js";
import { connectDevAssist, type DevAssistSession } from "./mcp.js";

const SYSTEM_PROMPT = `You are a concise developer assistant for Maej's learning tracker.

You have DevAssist MCP tools over a remote workspace:
- list_projects — list projects under WORKSPACE_ROOT
- search_code — search a project for a literal substring
- git_summary — read-only git status for a project

Rules:
- Prefer tools over guessing about the remote workspace.
- Quote paths from tool results (they prove the remote Render filesystem).
- After tools return enough evidence, give a clear final answer.
- Do not invent file contents you have not seen in tool results.`;

export type AgentRunResult = {
  text: string;
  stepsUsed: number;
  maxSteps: number;
  /** True when tool output mentioned /opt/render/ (remote evidence). */
  sawRemoteRenderPath: boolean;
};

/** Format tool output for the learning CLI (truncate very long blobs). */
function formatOutput(output: unknown, maxChars = 1200): string {
  const text = typeof output === "string" ? output : JSON.stringify(output, null, 2);
  if (text.length <= maxChars) return text;
  return `${text.slice(0, maxChars)}\n… (truncated)`;
}

/**
 * Print one generateText step so the agent loop is visible.
 *
 * A "step" here is one model response that may include tool calls; the SDK
 * executes tools and feeds results back before the next step.
 */
function printStep(
  stepIndex: number,
  step: {
    text?: string;
    toolCalls: Array<{ toolName: string; input: unknown; invalid?: boolean }>;
    toolResults: Array<{ toolName: string; output: unknown }>;
  },
): void {
  console.log(`\nStep ${stepIndex}`);

  if (step.toolCalls.length === 0) {
    console.log("Model → final answer (no tool call this step)");
    if (step.text?.trim()) {
      console.log(step.text.trim());
    }
    return;
  }

  for (const call of step.toolCalls) {
    if ("invalid" in call && call.invalid) {
      console.log(`Model → ${call.toolName} (INVALID arguments)`);
      continue;
    }
    console.log(`Model → ${call.toolName}`);
    console.log("Arguments:");
    console.log(JSON.stringify(call.input, null, 2));
  }

  for (const tr of step.toolResults) {
    console.log(`\nTool result (${tr.toolName}):`);
    console.log(formatOutput(tr.output));
  }

  if (step.text?.trim()) {
    console.log("\nModel note:");
    console.log(step.text.trim());
  }
}

/**
 * Run one agent task: connect MCP → give tools to the model → loop until
 * final text or MAX_STEPS.
 *
 * In-memory only: conversation/tool history lives inside `generateText` for
 * this single run (no DB / long-term memory).
 */
export async function runAgent(
  config: HarnessConfig,
  task: string,
): Promise<AgentRunResult> {
  let session: DevAssistSession | undefined;

  try {
    // --- Connect remote MCP (Streamable HTTP) ---
    console.log(`MCP: ${config.devassistUrl}`);
    console.log(`Model: ${config.openaiModel}`);
    console.log(`Max steps: ${config.maxSteps}`);

    session = await connectDevAssist(config);
    console.log(`Discovered tools: ${session.toolNames.join(", ")}`);

    const openrouter = createOpenAI({
      apiKey: config.openrouterApiKey,
      baseURL: config.openaiBaseUrl,
    });
    // Chat Completions — Responses API + free routers can hang on tool rounds.
    const model = openrouter.chat(config.openaiModel);

    let stepCounter = 0;

    // --- Agent loop (AI SDK multi-step generateText) ---
    // What the SDK does each step:
    //   1. Send messages + tool schemas to the LLM
    //   2. If the model returns tool calls → execute tool.execute() (MCP HTTPS)
    //   3. Append tool results to the in-memory message list
    //   4. Call the model again
    // stopWhen: stepCountIs(N) ends the loop after N model steps.
    const result = await generateText({
      model,
      tools: session.tools,
      system: SYSTEM_PROMPT,
      prompt: task,
      stopWhen: stepCountIs(config.maxSteps),
      maxRetries: 1,
      abortSignal: AbortSignal.timeout(180_000),
      onStepFinish: (step) => {
        stepCounter += 1;
        printStep(stepCounter, step);
      },
    });

    const sawRemoteRenderPath = JSON.stringify(result.steps).includes(
      "/opt/render/",
    );

    return {
      text: result.text?.trim() || "(empty final text)",
      stepsUsed: result.steps.length,
      maxSteps: config.maxSteps,
      sawRemoteRenderPath,
    };
  } finally {
    // Always release the MCP session — even on model/MCP errors.
    if (session) {
      await session.client.close().catch(() => undefined);
    }
  }
}
